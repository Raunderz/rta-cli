package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestSanitizeEnvID(t *testing.T) {
	tests := []struct {
		input string
		valid bool
	}{
		{"abc123", true},
		{"a1b2c3", true},
		{"", false},
		{"ABC123", false},
		{"abc-123", false},
		{"abc 123", false},
		{"abc123def456", true},
		{"abc123def45678901", false}, // 17 chars, > 16
		{"../../../etc/passwd", false},
		{"abc;rm -rf /", false},
		{"abc\x00def", false},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got := sanitizeEnvID(tt.input)
			if got != tt.valid {
				t.Errorf("sanitizeEnvID(%q) = %v, want %v", tt.input, got, tt.valid)
			}
		})
	}
}

func TestExtractIP(t *testing.T) {
	tests := []struct {
		name     string
		headers  map[string]string
		remote   string
		expected string
	}{
		{
			name:     "X-Forwarded-For",
			headers:  map[string]string{"X-Forwarded-For": "1.2.3.4, 5.6.7.8"},
			remote:   "127.0.0.1:12345",
			expected: "1.2.3.4, 5.6.7.8",
		},
		{
			name:     "X-Real-IP",
			headers:  map[string]string{"X-Real-IP": "9.10.11.12"},
			remote:   "127.0.0.1:12345",
			expected: "9.10.11.12",
		},
		{
			name:     "RemoteAddr fallback",
			headers:  map[string]string{},
			remote:   "192.168.1.1:8080",
			expected: "192.168.1.1",
		},
		{
			name:     "X-Forwarded-For takes priority",
			headers:  map[string]string{"X-Forwarded-For": "1.1.1.1", "X-Real-IP": "2.2.2.2"},
			remote:   "127.0.0.1:12345",
			expected: "1.1.1.1",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			r := httptest.NewRequest("GET", "/", nil)
			r.RemoteAddr = tt.remote
			for k, v := range tt.headers {
				r.Header.Set(k, v)
			}
			got := extractIP(r)
			if got != tt.expected {
				t.Errorf("extractIP() = %q, want %q", got, tt.expected)
			}
		})
	}
}

func TestFormatDuration(t *testing.T) {
	tests := []struct {
		seconds  float64
		expected string
	}{
		{30, "30s"},
		{90, "1m30s"},
		{3661, "1h1m"},
		{0, "0s"},
	}

	for _, tt := range tests {
		t.Run(tt.expected, func(t *testing.T) {
			d := time.Duration(tt.seconds * float64(time.Second))
			got := formatDuration(d)
			if got != tt.expected {
				t.Errorf("formatDuration(%v) = %q, want %q", d, got, tt.expected)
			}
		})
	}
}

func TestLimitBody(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	limited := limitBody(handler, 1024)

	// Request within limit
	body := strings.NewReader(strings.Repeat("a", 512))
	req := httptest.NewRequest("POST", "/", body)
	rec := httptest.NewRecorder()
	limited(rec, req)
	if rec.Code != http.StatusOK {
		t.Errorf("expected 200 for body within limit, got %d", rec.Code)
	}
}

func TestHandleStatus(t *testing.T) {
	req := httptest.NewRequest("GET", "/status", nil)
	rec := httptest.NewRecorder()
	handleStatus(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}

	body := rec.Body.String()
	if !strings.Contains(body, `"status":"healthy"`) {
		t.Errorf("expected healthy status, got %s", body)
	}
	if !strings.Contains(body, `"version"`) {
		t.Errorf("expected version field, got %s", body)
	}
}

func TestHandleListEnvsEmpty(t *testing.T) {
	// Reset envs for test
	envs.Range(func(k, v interface{}) bool {
		envs.Delete(k)
		return true
	})

	req := httptest.NewRequest("GET", "/envs", nil)
	rec := httptest.NewRecorder()
	handleListEnvs(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rec.Code)
	}

	body := rec.Body.String()
	if !strings.Contains(body, "[]") && !strings.Contains(body, "null") {
		t.Errorf("expected empty array or null, got %s", body)
	}
}

func TestHandleCreateEnvMethodNotAllowed(t *testing.T) {
	req := httptest.NewRequest("GET", "/env", nil)
	rec := httptest.NewRecorder()
	handleCreateEnv(rec, req)

	if rec.Code != http.StatusMethodNotAllowed {
		t.Errorf("expected 405, got %d", rec.Code)
	}
}

func TestHandleCreateEnvMissingAPIKey(t *testing.T) {
	req := httptest.NewRequest("POST", "/env", nil)
	rec := httptest.NewRecorder()
	handleCreateEnv(rec, req)

	if rec.Code != http.StatusUnauthorized {
		t.Errorf("expected 401, got %d", rec.Code)
	}

	body := rec.Body.String()
	if !strings.Contains(body, "Missing X-API-KEY") {
		t.Errorf("expected missing API key error, got %s", body)
	}
}

func TestHandleShellInvalidID(t *testing.T) {
	req := httptest.NewRequest("GET", "/ws/env/../../../etc/passwd", nil)
	rec := httptest.NewRecorder()
	handleShell(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", rec.Code)
	}
}

func TestHandleShellEnvNotFound(t *testing.T) {
	req := httptest.NewRequest("GET", "/ws/env/nonexistent", nil)
	rec := httptest.NewRecorder()
	handleShell(rec, req)

	if rec.Code != http.StatusNotFound {
		t.Errorf("expected 404, got %d", rec.Code)
	}
}

func TestHandleExposeInvalidID(t *testing.T) {
	req := httptest.NewRequest("POST", "/expose/../../etc/passwd/8080", nil)
	rec := httptest.NewRecorder()
	handleExpose(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", rec.Code)
	}
}

func TestHandleChatMethodNotAllowed(t *testing.T) {
	req := httptest.NewRequest("GET", "/env/chat/test123", nil)
	rec := httptest.NewRecorder()
	handleChat(rec, req)

	if rec.Code != http.StatusMethodNotAllowed {
		t.Errorf("expected 405, got %d", rec.Code)
	}
}

func TestHandleChatInvalidID(t *testing.T) {
	req := httptest.NewRequest("POST", "/env/chat/../../../etc", nil)
	rec := httptest.NewRecorder()
	handleChat(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", rec.Code)
	}
}

func TestHandleChatEnvNotFound(t *testing.T) {
	req := httptest.NewRequest("POST", "/env/chat/nonexistent", nil)
	rec := httptest.NewRecorder()
	handleChat(rec, req)

	if rec.Code != http.StatusNotFound {
		t.Errorf("expected 404, got %d", rec.Code)
	}
}
