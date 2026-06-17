package main

import (
	"log"
	"os/exec"
	"strings"
	"time"
)

func cleanupLoop() {
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		now := time.Now()
		var toDelete []*Env

		envs.Range(func(k, v interface{}) bool {
			env := v.(*Env)
			age := now.Sub(env.CreatedAt)
			idle := now.Sub(env.LastPing)

			if age > 3*time.Hour {
				log.Printf("⏱  Cleanup: env %s exceeded max lifetime (3h)", env.ID)
				toDelete = append(toDelete, env)
				return true
			}

			if idle > 30*time.Minute {
				log.Printf("⏱  Cleanup: env %s idle for 30m", env.ID)
				toDelete = append(toDelete, env)
				return true
			}

			return true
		})

		for _, env := range toDelete {
			deleteEnv(env)
		}
	}
}

func abuseDetectLoop() {
	ticker := time.NewTicker(3 * time.Minute)
	defer ticker.Stop()

	blacklist := []string{
		"xmrig", "miner", "stratum", "masscan", "nmap", "zmap",
		"hydra", "john", "hashcat", "nikto", "sqlmap",
		"metasploit", "aircrack", "airmon", "bettercap",
	}

	for range ticker.C {
		envs.Range(func(k, v interface{}) bool {
			env := v.(*Env)

			cmd := exec.Command("docker", "exec", env.Container, "ps", "aux")
			output, err := cmd.Output()
			if err != nil {
				return true
			}

			psOutput := strings.ToLower(string(output))

			for _, pattern := range blacklist {
				if strings.Contains(psOutput, pattern) {
					log.Printf("🚨 ABUSE: env %s detected %s", env.ID, pattern)
					deleteEnv(env)
					logEvent("abuse_detected", env.ID, pattern)
					return true
				}
			}

			return true
		})
	}
}

func rateLimitResetLoop() {
	ticker := time.NewTicker(1 * time.Hour)
	defer ticker.Stop()

	for range ticker.C {
		var ips []string
		rateLimits.Range(func(k, v interface{}) bool {
			ips = append(ips, k.(string))
			return true
		})

		for _, ip := range ips {
			rateLimits.Delete(ip)
		}

		log.Printf("🔄 Rate limits reset (%d IPs)", len(ips))
	}
}
