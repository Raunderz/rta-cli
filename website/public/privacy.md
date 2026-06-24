# Privacy Policy

**Last Updated: June 24, 2026**

This Privacy Policy describes how Rta ("we," "us," or "our") collects, uses, and protects your information when you use our Service.

## 1. Information We Collect

### 1.1 Account Information
When you create an account, we collect:
- **Email address** (from GitHub OAuth or email/password registration)
- **Username** (provided by you or derived from GitHub)
- **GitHub profile information** (if using GitHub OAuth): profile photo, public profile data

### 1.2 Authentication Data
- **OAuth tokens** (GitHub access/refresh tokens, stored securely)
- **API keys** (hashed for verification, stored in our database)
- **Session cookies** (for maintaining your login session)

### 1.3 Usage Data
We automatically collect:
- **API call metadata**: timestamps, endpoints called, response codes
- **Token usage**: prompt tokens, completion tokens per request
- **Model information**: which AI model was used for each request
- **Provider information**: which AI provider handled each request
- **Latency metrics**: request/response timing
- **Device information**: IP address, user agent, device type
- **Error logs**: stack traces and error messages (with secrets redacted)

### 1.4 AI Interaction Data
- **Prompts and responses**: logged for debugging and system optimization
- **Tool calls**: which tools were invoked during AI sessions
- **Session context**: conversation history within a session

**Important**: All AI interaction data is automatically scrubbed of:
- API keys and secrets (AWS, GCP, GitHub, Stripe, etc.)
- Local file paths (e.g., `/home/[USER]`)
- Personal identifiers where detectable

### 1.5 Payment Information
- **Billing details**: processed by Stripe (we do not store card numbers)
- **Transaction history**: payment amounts, dates, plan changes

### 1.6 Cloud Environment Data
When you use cloud development environments:
- **Workspace files**: code and files you upload to containers
- **Terminal sessions**: commands executed in cloud terminals
- **Container metadata**: creation time, resource usage, lifecycle events

## 2. How We Collect Information

- **Directly from you**: account registration, profile updates, support requests
- **Automatically**: API usage logging, analytics, error tracking
- **From third parties**: GitHub (OAuth), Stripe (payments), AI providers (model responses)

## 3. How We Use Your Information

### 3.1 Service Delivery
- Authenticate and authorize your access
- Process AI requests and route to appropriate providers
- Manage cloud development environments
- Process payments and manage subscriptions

### 3.2 System Improvement
- Debug and fix issues
- Optimize AI model routing and performance
- Improve system reliability and speed
- Monitor for abuse and security threats

### 3.3 Communication
- Send account-related notifications (security alerts, billing)
- Respond to support requests
- Notify about service updates (with opt-out for non-essential communications)

### 3.4 Legal Compliance
- Comply with applicable laws and regulations
- Respond to legal requests when required

## 4. Legal Basis for Processing (GDPR)

For users in the European Economic Area:

| Processing Activity | Legal Basis |
|---------------------|-------------|
| Account creation and management | Contract performance |
| AI request processing | Contract performance |
| Usage analytics | Legitimate interest (service improvement) |
| Security monitoring | Legitimate interest (platform security) |
| Payment processing | Contract performance |
| Marketing communications | Consent (opt-in) |

## 5. Information Sharing

### 5.1 We Do Not Sell Your Data
We do not sell, rent, or trade your personal information to third parties for marketing purposes.

### 5.2 Service Providers
We share data with service providers who assist in operating our Service:

| Provider | Purpose | Data Shared |
|----------|---------|-------------|
| **Supabase** | Authentication, database | Account data, API keys (hashed) |
| **Vercel** | Website hosting, analytics | Usage data, IP addresses |
| **Stripe** | Payment processing | Billing information |
| **AI Providers** (Groq, Cerebras, SambaNova, OpenRouter, Gemini) | AI model inference | Prompts, conversation context |
| **Cloudflare** | Tunneling services | Network metadata |

### 5.3 Legal Requirements
We may disclose information if required by law, court order, or governmental authority.

### 5.4 Business Transfers
In the event of a merger, acquisition, or sale of assets, your data may be transferred. We will notify you before your data becomes subject to a different privacy policy.

## 6. Cookies and Tracking

### 6.1 Essential Cookies
- **Session cookies**: Maintain your login session
- **OAuth cookies**: Temporary cookies for GitHub authentication flow (deleted after use)

### 6.2 Analytics
- **Vercel Analytics**: Anonymous usage statistics (page views, performance metrics)
- No third-party advertising cookies or tracking pixels

### 6.3 Local Storage
- **API key hints**: Stored locally in your browser for convenience
- **Theme preferences**: UI customization settings
- **Conversation history**: Chat history stored locally in your browser (not sent to us)

## 7. Data Retention

| Data Type | Retention Period |
|-----------|-----------------|
| Account information | Until account deletion |
| API keys | Until deleted by user |
| Usage/telemetry logs | 90 days |
| AI interaction logs | 90 days |
| Payment records | 7 years (legal requirement) |
| Cloud environment data | Until session ends + 24 hours |
| Support tickets | 2 years |

## 8. Data Security

We implement industry-standard security measures:

- **Encryption in transit**: All data transmitted over TLS/HTTPS
- **Encryption at rest**: Database encryption for stored data
- **Authentication**: Secure OAuth 2.0 with PKCE flow
- **API key security**: Keys are hashed (SHA-256) before storage
- **Secret scrubbing**: Automatic removal of credentials from logs
- **Access controls**: Strict internal access controls on user data
- **Container isolation**: Cloud environments run with dropped capabilities and resource limits

**Important**: No method of transmission or storage is 100% secure. While we strive to protect your data, we cannot guarantee absolute security.

## 9. Your Rights

### 9.1 All Users
You have the right to:
- **Access** your personal data
- **Correct** inaccurate data
- **Delete** your account and associated data
- **Export** your data in a portable format
- **Object** to processing of your data
- **Withdraw consent** where processing is based on consent

### 9.2 European Economic Area (GDPR)
Additional rights under GDPR:
- **Right to restrict processing**
- **Right to data portability**
- **Right to lodge a complaint** with your local supervisory authority

### 9.3 California Residents (CCPA/CPRA)
Under the California Consumer Privacy Act:
- **Right to know** what personal information is collected
- **Right to delete** personal information
- **Right to opt-out** of sale of personal information (we do not sell data)
- **Right to non-discrimination** for exercising your rights

### 9.4 How to Exercise Your Rights
Contact us at privacy@rta.dev or through the support portal. We will respond to requests within 30 days.

## 10. Children's Privacy

Rta is not intended for users under 13 years of age. We do not knowingly collect data from children under 13. If we discover that a child under 13 has provided us with personal information, we will delete it immediately.

## 11. International Data Transfers

Your data may be processed in countries other than your own. We ensure appropriate safeguards are in place:
- Standard Contractual Clauses (SCCs) for EU data transfers
- Service providers are contractually required to protect your data

## 12. Changes to This Policy

We may update this Privacy Policy from time to time. Material changes will be:
- Posted on this page with an updated "Last Updated" date
- Notified via email or prominent notice on the Service at least 30 days before taking effect

We encourage you to review this policy periodically.

## 13. Contact Us

For privacy-related inquiries:
- **Email**: privacy@rta.dev
- **Data Protection Officer**: dpo@rta.dev
- **Website**: [rta-three.vercel.app/privacy](https://rta-three.vercel.app/privacy)

For general inquiries: support@rta.dev

---

**NOTICE**: This privacy policy is provided as a template and should be reviewed by qualified legal counsel before publication. Rta does not provide legal advice.
