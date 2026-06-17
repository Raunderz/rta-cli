package main

import (
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

var startTime = time.Now()

func main() {
	mux := http.NewServeMux()

	// Routes
	mux.HandleFunc("/env", rateLimit(limitBody(handleCreateEnv, 1024*1024)))
	mux.HandleFunc("/env/", rateLimit(limitBody(handleEnvAction, 100*1024*1024)))
	mux.HandleFunc("/ws/env/", handleShell)
	mux.HandleFunc("/env/chat/", rateLimit(limitBody(handleChat, 10*1024)))
	mux.HandleFunc("/expose/", rateLimit(limitBody(handleExpose, 1024)))
	mux.HandleFunc("/envs", rateLimit(limitBody(handleListEnvs, 1024)))
	mux.HandleFunc("/status", rateLimit(limitBody(handleStatus, 1024)))
	mux.Handle("/", http.FileServer(http.Dir("./public")))

	// Background goroutines
	go cleanupLoop()
	go abuseDetectLoop()
	go rateLimitResetLoop()

	server := &http.Server{
		Addr:              ":8080",
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       15 * time.Second,
		WriteTimeout:      30 * time.Second,
		IdleTimeout:       120 * time.Second,
		MaxHeaderBytes:    1 << 20,
	}

	// Graceful shutdown
	go func() {
		sigCh := make(chan os.Signal, 1)
		signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
		sig := <-sigCh
		log.Printf("🛑 Received %s, shutting down...", sig)

		// Delete all containers before exit
		envs.Range(func(k, v interface{}) bool {
			env := v.(*Env)
			deleteEnv(env)
			return true
		})

		server.Close()
	}()

	log.Printf("🚀 TempDev starting on :8080")
	log.Fatal(server.ListenAndServe())
}
