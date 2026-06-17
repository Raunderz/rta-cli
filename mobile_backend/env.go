package main

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os/exec"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

type Env struct {
	ID        string          `json:"id"`
	UserID    string          `json:"user_id"`
	APIKey    string          `json:"-"`
	Container string          `json:"-"`
	CreatedAt time.Time       `json:"created_at"`
	LastPing  time.Time       `json:"last_ping"`
	TunnelURL string          `json:"tunnel_url,omitempty"`
	TunnelPID int             `json:"-"`
	mu        sync.Mutex      `json:"-"`
	WS        *websocket.Conn `json:"-"`
}

var envs = sync.Map{}

func generateID() string {
	b := make([]byte, 4)
	rand.Read(b)
	return hex.EncodeToString(b)
}

func sanitizeEnvID(id string) bool {
	if len(id) == 0 || len(id) > 16 {
		return false
	}
	for _, c := range id {
		if !((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')) {
			return false
		}
	}
	return true
}

func createContainer(id string) (string, error) {
	cmd := exec.Command("docker", "run", "-d",
		"--memory=512m",
		"--memory-swap=512m",
		"--cpus=0.5",
		"--pids-limit=64",
		"--cap-drop=ALL",
		"--security-opt=no-new-privileges",
		"--add-host", "aws-metadata:169.254.169.254",
		"-u", "dev",
		"tempdev:latest",
		"sleep", "infinity",
	)

	output, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(output)), nil
}

func deleteEnv(env *Env) {
	logEventToBackend(env.APIKey, "env_deleted", env.ID, nil)

	if err := exec.Command("docker", "rm", "-f", env.Container).Run(); err != nil {
		log.Printf("docker rm failed for env %s: %v", env.ID, err)
	}

	if env.TunnelPID > 0 {
		if err := exec.Command("kill", "-9", fmt.Sprintf("%d", env.TunnelPID)).Run(); err != nil {
			log.Printf("kill tunnel PID %d failed: %v", env.TunnelPID, err)
		}
	}

	envs.Delete(env.ID)
	logEvent("env_deleted", env.ID, "")
	log.Printf("✗ Deleted env %s", env.ID)
}

func findEnvByUser(userID string) *Env {
	var found *Env
	envs.Range(func(k, v interface{}) bool {
		env := v.(*Env)
		if env.UserID == userID {
			found = env
			return false
		}
		return true
	})
	return found
}

func verifyEnvAccess(r *http.Request, env *Env) bool {
	apiKey := r.Header.Get("X-API-KEY")
	if apiKey == "" {
		apiKey = r.URL.Query().Get("api_key")
	}
	return apiKey == env.APIKey
}

func writeJSON(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}
