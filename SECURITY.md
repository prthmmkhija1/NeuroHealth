# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of NeuroHealth seriously. If you discover a security vulnerability, please follow these steps:

### Do NOT

- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it has been addressed

### Do

1. **Email the maintainers** with details of the vulnerability
2. **Include the following information:**
   - Type of vulnerability (e.g., injection, XSS, data exposure)
   - Full path of the affected source file(s)
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact assessment

### Response Timeline

- **Initial Response:** Within 48 hours
- **Status Update:** Within 7 days
- **Resolution:** Typically within 30 days, depending on complexity

### Safe Harbor

We consider security research conducted in accordance with this policy to be:

- Authorized concerning any applicable anti-hacking laws
- Exempt from restrictions in our Terms of Service that would interfere with security research

## Security Considerations for NeuroHealth

### Medical Data Privacy

NeuroHealth is designed as a **demonstration system** and should NOT be used with real patient data in production without proper compliance measures:

- No PHI (Protected Health Information) should be stored
- All conversations are ephemeral by default
- No user authentication or data persistence is implemented

### LLM Safety Guardrails

The system includes safety guardrails to:

- Detect and escalate emergency situations
- Prevent harmful medical advice
- Block jailbreak attempts
- Refuse out-of-scope requests

### API Security

When deploying the API:

- Use HTTPS in production
- Implement rate limiting
- Add authentication for production use
- Sanitize all user inputs

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who help improve NeuroHealth's security.
