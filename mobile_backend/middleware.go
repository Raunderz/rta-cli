package main

import (
	"log"
	"net/http"
	"strings"
	"sync"
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
	count int
	start time.Time
}

func checkRateLimit(ip string) bool {
	val, _ := rateLimits.Load(ip)
	if val != nil {
		entry := val.(*rateLimitEntry)
		if time.Since(entry.start) < rateLimitWindow {
			if entry.count >= rateLimitMax {
				return false
			}
			entry.count++
			return true
		}
		rateLimits.Store(ip, &rateLimitEntry{count: 1, start: time.Now()})
		return true
	}
	rateLimits.Store(ip, &rateLimitEntry{count: 1, start: time.Now()})
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
	ip := r.Header.Get("X-Forwarded-For")
	if ip == "" {
		ip = r.Header.Get("X-Real-IP")
	}
	if ip == "" {
		ip = strings.Split(r.RemoteAddr, ":")[0]
	}
	return ip
}
