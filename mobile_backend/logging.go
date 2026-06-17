package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"
)

func logEvent(eventType, envID, detail string) {
	logMutex.Lock()
	defer logMutex.Unlock()

	logEntry := map[string]interface{}{
		"timestamp": time.Now().UTC().Format(time.RFC3339),
		"event":     eventType,
		"env_id":    envID,
		"detail":    detail,
	}

	data, _ := json.Marshal(logEntry)

	file, err := os.OpenFile("events.log", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Printf("Failed to log event: %v", err)
		return
	}
	defer file.Close()
	file.Write(append(data, '\n'))
}

func formatDuration(d time.Duration) string {
	total := int(d.Seconds())
	hours := total / 3600
	minutes := (total % 3600) / 60
	seconds := total % 60

	if hours > 0 {
		return fmt.Sprintf("%dh%dm", hours, minutes)
	}
	if minutes > 0 {
		return fmt.Sprintf("%dm%ds", minutes, seconds)
	}
	return fmt.Sprintf("%ds", seconds)
}
