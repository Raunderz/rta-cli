package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"time"

	"github.com/gorilla/websocket"
)

func handleCreateEnv(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "POST only", http.StatusMethodNotAllowed)
		return
	}

	apiKey := r.Header.Get("X-API-KEY")
	if apiKey == "" {
		http.Error(w, "Missing X-API-KEY", http.StatusUnauthorized)
		return
	}

	user, err := verifyKey(apiKey)
	if err != nil {
		http.Error(w, "Invalid API key", http.StatusUnauthorized)
		return
	}

	if user.Tier == "free" {
		http.Error(w, "Free tier access denied. Upgrade for sandbox access.", http.StatusForbidden)
		return
	}

	if existing := findEnvByUser(user.UserID); existing != nil {
		writeJSON(w, map[string]string{
			"id":     existing.ID,
			"ws_url": "/ws/env/" + existing.ID,
		})
		return
	}

	id := generateID()
	container, err := createContainer(id)
	if err != nil {
		log.Printf("docker run failed: %v", err)
		logEvent("create_failed", id, err.Error())
		http.Error(w, "Failed to create environment", http.StatusInternalServerError)
		return
	}

	env := &Env{
		ID:        id,
		UserID:    user.UserID,
		APIKey:    apiKey,
		Container: container,
		CreatedAt: time.Now(),
		LastPing:  time.Now(),
	}

	envs.Store(id, env)
	logEventToBackend(apiKey, "env_created", id, map[string]interface{}{"tier": user.Tier})
	logEvent("env_created", id, container[:12])
	log.Printf("✓ Created env %s for user %s (%s)", id, user.UserID, user.Tier)

	writeJSON(w, map[string]string{
		"id":     id,
		"ws_url": "/ws/env/" + id,
	})
}

func handleEnvAction(w http.ResponseWriter, r *http.Request) {
	pathParts := strings.Split(strings.TrimPrefix(r.URL.Path, "/env/"), "/")
	id := pathParts[0]

	if !sanitizeEnvID(id) {
		http.Error(w, "Invalid env ID", http.StatusBadRequest)
		return
	}

	val, ok := envs.Load(id)
	if !ok {
		http.Error(w, "Environment not found", http.StatusNotFound)
		return
	}

	env := val.(*Env)

	if !verifyEnvAccess(r, env) {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	action := ""
	if len(pathParts) > 1 {
		action = pathParts[1]
	}

	if action == "upload" && r.Method == "POST" {
		handleUpload(w, r, env)
		return
	}

	if action == "download" && r.Method == "GET" {
		handleDownload(w, r, env)
		return
	}

	switch r.Method {
	case "GET":
		writeJSON(w, env)
	case "DELETE":
		deleteEnv(env)
		w.WriteHeader(http.StatusNoContent)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

func handleUpload(w http.ResponseWriter, r *http.Request, env *Env) {
	file, _, err := r.FormFile("workspace")
	if err != nil {
		http.Error(w, "Error retrieving file from form-data", http.StatusBadRequest)
		return
	}
	defer file.Close()

	tmpPath := fmt.Sprintf("/tmp/%s.zip", env.ID)
	out, err := os.Create(tmpPath)
	if err != nil {
		http.Error(w, "Failed to create temp file", http.StatusInternalServerError)
		return
	}
	io.Copy(out, file)
	out.Close()

	if err := exec.Command("docker", "cp", tmpPath, fmt.Sprintf("%s:/tmp/workspace.zip", env.Container)).Run(); err != nil {
		log.Printf("docker cp to container failed: %v", err)
		http.Error(w, "Failed to copy workspace to container", http.StatusInternalServerError)
		return
	}

	unzipCmd := exec.Command("docker", "exec", "-u", "root", env.Container, "bash", "-c",
		"mkdir -p /workspace && chown dev:dev /workspace && python3 -c 'import zipfile, os; zf=zipfile.ZipFile(\"/tmp/workspace.zip\",\"r\"); dest=\"/workspace\"; [zf.extract(info,dest) for info in zf.infolist() if not os.path.realpath(os.path.join(dest,info.filename)).startswith(os.path.realpath(dest)+\"/\") and not os.path.realpath(os.path.join(dest,info.filename))==os.path.realpath(dest)]' && chown -R dev:dev /workspace && rm /tmp/workspace.zip")
	if err := unzipCmd.Run(); err != nil {
		log.Printf("Unzip failed: %v", err)
		http.Error(w, "Failed to extract workspace in container", http.StatusInternalServerError)
		return
	}

	// ZIP bomb protection
	sizeCmd := exec.Command("docker", "exec", env.Container, "du", "-sm", "/workspace")
	sizeOutput, err := sizeCmd.Output()
	if err == nil {
		var sizeMB int
		fmt.Sscanf(strings.TrimSpace(string(sizeOutput)), "%d", &sizeMB)
		if sizeMB > 500 {
			log.Printf("⚠️ ZIP bomb detected: env %s extracted to %dMB (limit 500MB)", env.ID, sizeMB)
			exec.Command("docker", "exec", env.Container, "rm", "-rf", "/workspace").Run()
			http.Error(w, "Workspace too large after extraction (limit 500MB)", http.StatusRequestEntityTooLarge)
			return
		}
	}

	os.Remove(tmpPath)
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("Workspace uploaded successfully"))
}

func handleDownload(w http.ResponseWriter, r *http.Request, env *Env) {
	tmpPath := fmt.Sprintf("/tmp/out_%s.zip", env.ID)

	script := `import os, zipfile
if os.path.exists("/workspace"):
    with zipfile.ZipFile("/tmp/workspace_out.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk("/workspace"):
            dirs[:] = [d for d in dirs if d not in (".venv", "node_modules", "__pycache__", ".git", ".expo")]
            for f in files:
                zf.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), "/workspace"))
`
	zipCmd := exec.Command("docker", "exec", "-u", "root", env.Container, "bash", "-c",
		fmt.Sprintf("echo '%s' > /tmp/zip.py && python3 /tmp/zip.py", script))
	if err := zipCmd.Run(); err != nil {
		log.Printf("Zip failed: %v", err)
		http.Error(w, "Failed to zip workspace", http.StatusInternalServerError)
		return
	}

	if err := exec.Command("docker", "cp", fmt.Sprintf("%s:/tmp/workspace_out.zip", env.Container), tmpPath).Run(); err != nil {
		log.Printf("docker cp from container failed: %v", err)
		http.Error(w, "Failed to copy workspace from container", http.StatusInternalServerError)
		return
	}
	defer os.Remove(tmpPath)

	w.Header().Set("Content-Type", "application/zip")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"workspace_%s.zip\"", env.ID))
	http.ServeFile(w, r, tmpPath)
}

func handleChat(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "POST only", http.StatusMethodNotAllowed)
		return
	}

	id := strings.TrimPrefix(r.URL.Path, "/env/chat/")
	if !sanitizeEnvID(id) {
		http.Error(w, "Invalid env ID", http.StatusBadRequest)
		return
	}

	val, ok := envs.Load(id)
	if !ok {
		http.Error(w, "Environment not found", http.StatusNotFound)
		return
	}
	env := val.(*Env)

	if !verifyEnvAccess(r, env) {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	var req struct {
		Prompt string `json:"prompt"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "text/plain")
	w.Header().Set("Transfer-Encoding", "chunked")

	cmd := exec.Command("docker", "exec",
		"-e", "rta_api_key="+env.APIKey,
		env.Container,
		"rta", "ask", req.Prompt, "--workspace", "/workspace",
	)

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		http.Error(w, "Failed to capture stdout", http.StatusInternalServerError)
		return
	}
	cmd.Stderr = os.Stderr

	if err := cmd.Start(); err != nil {
		http.Error(w, "Failed to start rta", http.StatusInternalServerError)
		return
	}

	buffer := make([]byte, 512)
	for {
		n, err := stdout.Read(buffer)
		if n > 0 {
			w.Write(buffer[:n])
			if f, ok := w.(http.Flusher); ok {
				f.Flush()
			}
		}
		if err != nil {
			break
		}
	}

	cmd.Wait()
	logEventToBackend(env.APIKey, "chat_prompt", env.ID, map[string]interface{}{"prompt": req.Prompt})
}

func handleExpose(w http.ResponseWriter, r *http.Request) {
	parts := strings.Split(strings.TrimPrefix(r.URL.Path, "/expose/"), "/")
	if len(parts) < 1 {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	id := parts[0]
	if !sanitizeEnvID(id) {
		http.Error(w, "Invalid env ID", http.StatusBadRequest)
		return
	}

	val, ok := envs.Load(id)
	if !ok {
		http.Error(w, "Environment not found", http.StatusNotFound)
		return
	}
	env := val.(*Env)

	if !verifyEnvAccess(r, env) {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	if r.Method == "DELETE" {
		if err := exec.Command("docker", "exec", env.Container, "pkill", "cloudflared").Run(); err != nil {
			log.Printf("pkill cloudflared failed for env %s: %v", env.ID, err)
		}
		env.TunnelURL = ""
		log.Printf("🛑 Unexposed env %s", id)
		w.WriteHeader(http.StatusNoContent)
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	if len(parts) < 2 {
		http.Error(w, "Port required", http.StatusBadRequest)
		return
	}
	port := parts[1]

	portNum, err := strconv.Atoi(port)
	if err != nil || portNum < 1 || portNum > 65535 {
		http.Error(w, "Port must be between 1 and 65535", http.StatusBadRequest)
		return
	}

	cmdStr := fmt.Sprintf(`
cloudflared tunnel --no-autoupdate --url http://localhost:%s > /tmp/tunnel.log 2>&1 &
`, port)

	startCmd := exec.Command("docker", "exec", env.Container, "bash", "-c", cmdStr)
	if err := startCmd.Run(); err != nil {
		log.Printf("cloudflared start failed: %v", err)
	}

	// Poll for URL (max 10 seconds)
	tunnelURL := ""
	for i := 0; i < 20; i++ {
		time.Sleep(500 * time.Millisecond)
		catCmd := exec.Command("docker", "exec", env.Container, "cat", "/tmp/tunnel.log")
		output, err := catCmd.Output()
		if err != nil {
			continue
		}

		if i%4 == 0 {
			log.Printf("Debug: Tunnel log poll %d: %s", i, string(output))
		}

		lines := strings.Split(string(output), "\n")
		for _, line := range lines {
			if strings.Contains(line, "trycloudflare.com") {
				idx := strings.Index(line, "https://")
				if idx != -1 {
					endIdx := strings.Index(line[idx:], " ")
					if endIdx == -1 {
						tunnelURL = strings.TrimSpace(line[idx:])
					} else {
						tunnelURL = strings.TrimSpace(line[idx : idx+endIdx])
					}
					tunnelURL = strings.TrimRight(tunnelURL, " |")
					if tunnelURL != "" {
						break
					}
				}
			}
		}
		if tunnelURL != "" {
			break
		}
	}

	if tunnelURL == "" {
		tunnelURL = "(Cloudflared still starting... refresh in a few seconds)"
	}

	env.TunnelURL = tunnelURL

	if tunnelURL != "" && !strings.Contains(tunnelURL, "starting") {
		env.mu.Lock()
		if env.WS != nil {
			msg := map[string]interface{}{
				"type": "tunnel",
				"url":  tunnelURL,
				"port": port,
			}
			data, _ := json.Marshal(msg)
			env.WS.WriteMessage(websocket.TextMessage, data)
		}
		env.mu.Unlock()
		logEventToBackend(env.APIKey, "tunnel_created", env.ID, map[string]interface{}{"port": port, "url": tunnelURL})
	}

	logEvent("tunnel_created", env.ID, port)
	log.Printf("🔗 Exposed port %s for env %s: %s", port, id, tunnelURL)

	writeJSON(w, map[string]string{
		"tunnel_url": tunnelURL,
		"port":       port,
		"note":       "Cloudflared generates a unique HTTPS URL. If not shown, wait 10-15 seconds and refresh.",
		"how_to":     "Inside terminal, run: cloudflared tunnel --url http://localhost:PORT to see the URL",
	})
}

func handleStatus(w http.ResponseWriter, r *http.Request) {
	count := 0
	envs.Range(func(k, v interface{}) bool {
		count++
		return true
	})

	writeJSON(w, map[string]interface{}{
		"status":          "healthy",
		"version":         "1.0.0",
		"active_sessions": count,
		"uptime":          formatDuration(time.Since(startTime)),
	})
}

func handleListEnvs(w http.ResponseWriter, r *http.Request) {
	type EnvStatus struct {
		ID        string `json:"id"`
		CreatedAt string `json:"created_at"`
		LastPing  string `json:"last_ping"`
		Uptime    string `json:"uptime"`
		Idle      string `json:"idle"`
		TunnelURL string `json:"tunnel_url,omitempty"`
	}

	apiKey := r.Header.Get("X-API-KEY")
	if apiKey == "" {
		http.Error(w, "Missing X-API-KEY", http.StatusUnauthorized)
		return
	}

	user, err := verifyKey(apiKey)
	if err != nil {
		http.Error(w, "Invalid API key", http.StatusUnauthorized)
		return
	}

	var envList []*EnvStatus
	now := time.Now()

	envs.Range(func(k, v interface{}) bool {
		env := v.(*Env)
		if env.UserID != user.UserID {
			return true
		}

		age := now.Sub(env.CreatedAt)
		idle := now.Sub(env.LastPing)

		envList = append(envList, &EnvStatus{
			ID:        env.ID,
			CreatedAt: env.CreatedAt.Format(time.RFC3339),
			LastPing:  env.LastPing.Format(time.RFC3339),
			Uptime:    formatDuration(age),
			Idle:      formatDuration(idle),
			TunnelURL: env.TunnelURL,
		})

		return true
	})

	writeJSON(w, envList)
}
