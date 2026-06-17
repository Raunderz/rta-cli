import { Component } from 'preact';

export default class ErrorBoundary extends Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style="min-height: 60vh; display: flex; align-items: center; justify-content: center; padding: 2rem;">
          <div style="max-width: 500px; text-align: center;">
            <h2 style="margin-bottom: 1rem; font-size: 1.5rem;">Something went wrong</h2>
            <p style="color: var(--text-secondary); margin-bottom: 2rem; font-size: 0.9rem;">
              {this.state.error?.message || "An unexpected error occurred."}
            </p>
            <a href="/" class="btn btn-primary">Go home</a>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
