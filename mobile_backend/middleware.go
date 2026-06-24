package main

import (
	"log"
	"net/http"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

var (
	rateLimits = sync.Map{}
	logMutex   = sync.Mutex{}
)

const (
	rateLimitMax    = 60
	rateLimitWindow = 1 * time.Minute
)

type rateLimitEntry struct {
	count atomic.Int32
	start time.Time
}

func checkRateLimit(ip string) bool {
	val, _ := rateLimits.Load(ip)
	if val != nil {
		entry := val.(*rateLimitEntry)
		if time.Since(entry.start) < rateLimitWindow {
			if entry.count.Add(1) > int32(rateLimitMax) {
				return false
			}
			return true
		}
		newEntry := &rateLimitEntry{start: time.Now()}
		newEntry.count.Store(1)
		rateLimits.Store(ip, newEntry)
		return true
	}
	newEntry := &rateLimitEntry{start: time.Now()}
	newEntry.count.Store(1)
	rateLimits.Store(ip, newEntry)
	return true
}

func rateLimit(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ip := extractIP(r)
		if !checkRateLimit(ip) {
			log.Printf("🚫 Rate limit exceeded for %s", ip)
			http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
			return
		}
		next(w, r)
	}
}

func limitBody(h http.HandlerFunc, maxBytes int64) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		r.Body = http.MaxBytesReader(w, r.Body, maxBytes)
		h(w, r)
	}
}

func extractIP(r *http.Request) string {
	// Use only RemoteAddr to prevent rate-limit bypass via X-Forwarded-For spoofing.
	// The backend is directly exposed (no trusted proxy), so forwarded headers are untrusted.
	ip := r.RemoteAddr
	if idx := strings.LastIndex(ip, ":"); idx != -1 {
		ip = ip[:idx]
	}
	return ip
}
