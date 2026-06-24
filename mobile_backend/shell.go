package main

import (
	"crypto/subtle"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/creack/pty"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		origin := r.Header.Get("Origin")
		if origin == "" {
			return true
		}
		allowed := []string{
			"http://localhost:5173",
			"https://rta-three.vercel.app",
			"http://localhost:1420",
			"null",
		}
		for _, a := range allowed {
			if origin == a {
				return true
			}
		}
		log.Printf("⚠️ Blocked WebSocket Origin: %s", origin)
		return false
	},
}

func handleShell(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimPrefix(r.URL.Path, "/ws/env/")

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

	apiKey := r.Header.Get("X-API-KEY")
	if apiKey == "" {
		apiKey = r.URL.Query().Get("api_key")
	}
	if apiKey == "" {
		proto := r.Header.Get("Sec-WebSocket-Protocol")
		if strings.HasPrefix(proto, "Bearer ") {
			apiKey = strings.TrimPrefix(proto, "Bearer ")
		} else if proto != "" {
			apiKey = proto
		}
	}

	if subtle.ConstantTimeCompare([]byte(apiKey), []byte(env.APIKey)) != 1 {
		log.Printf("🚫 Unauthorized shell access attempt for env %s", id)
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	subprotocol := r.Header.Get("Sec-WebSocket-Protocol")
	conn, err := upgrader.Upgrade(w, r, http.Header{
		"Sec-WebSocket-Protocol": []string{subprotocol},
	})
	if err != nil {
		log.Printf("WebSocket upgrade failed: %v", err)
		return
	}
	defer conn.Close()

	env.mu.Lock()
	env.WS = conn
	env.mu.Unlock()

	defer func() {
		env.mu.Lock()
		env.WS = nil
		env.mu.Unlock()
	}()

	bash := exec.Command("docker", "exec", "-it", env.Container, "bash")
	bash.Env = append(os.Environ(), "TERM=xterm")

	ptmx, err := pty.Start(bash)
	if err != nil {
		log.Printf("PTY failed: %v", err)
		conn.WriteMessage(websocket.BinaryMessage, []byte("Error: "+err.Error()))
		return
	}
	defer ptmx.Close()
	defer bash.Process.Kill()

	// Client input → container
	go func() {
		for {
			_, msg, err := conn.ReadMessage()
			if err != nil {
				return
			}

			if len(msg) > 0 && msg[0] == '{' {
				var resize struct {
					Cols uint16 `json:"cols"`
					Rows uint16 `json:"rows"`
				}
				if err := json.Unmarshal(msg, &resize); err == nil {
					pty.Setsize(ptmx, &pty.Winsize{
						Cols: resize.Cols,
						Rows: resize.Rows,
					})
					continue
				}
			}

			ptmx.Write(msg)
			env.LastPing = time.Now()
		}
	}()

	logEventToBackend(env.APIKey, "shell_opened", env.ID, nil)

	// Container output → client
	buf := make([]byte, 4096)
	for {
		n, err := ptmx.Read(buf)
		if err != nil {
			break
		}
		if n > 0 {
			if err := conn.WriteMessage(websocket.BinaryMessage, buf[:n]); err != nil {
				break
			}
		}
	}

	logEventToBackend(env.APIKey, "shell_closed", env.ID, nil)
	logEvent("shell_closed", env.ID, "")
}
