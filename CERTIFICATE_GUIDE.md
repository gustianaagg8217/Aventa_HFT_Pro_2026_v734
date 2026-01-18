# Aventa HFT Pro 2026 - Code Signing Certificate Guide

## �️ Prerequisites

### **Required Tools Installation:**

1. **Windows SDK** (for signtool):
   ```batch
   # Download Windows SDK from:
   # https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/
   # Or install Visual Studio Build Tools
   ```

2. **Verify signtool installation**:
   ```batch
   where signtool
   # Should show: C:\Program Files (x86)\Windows Kits\10\bin\...\signtool.exe
   ```

## �📋 Certificate Types

### 1. **Self-Signed Certificate** (Development Only)
- **Purpose**: Development and testing
- **Trust Level**: Not trusted by Windows (shows warning)
- **Cost**: Free
- **Validity**: Unlimited (but not trusted)
- **Usage**: Development environment only

**Created Certificate:**
- Subject: CN=PT Aventa Intelligent Power
- Thumbprint: 3152A250B85E1AB0CDD1804146D80DC2D1EF1984
- Location: Current User\Personal

### 2. **Standard Code Signing Certificate**
- **Purpose**: Production software signing
- **Trust Level**: Trusted by Windows
- **Cost**: $200-500/year
- **Validity**: 1-3 years
- **Usage**: Commercial software distribution

### 3. **EV Code Signing Certificate** (Extended Validation)
- **Purpose**: High-trust software signing
- **Trust Level**: Trusted + shows publisher name in green
- **Cost**: $500-1000/year
- **Validity**: 1-2 years
- **Usage**: Enterprise software, financial applications

## 🛒 Recommended Certificate Authorities

### **Primary Recommendation: DigiCert**
- **Website**: https://www.digicert.com/code-signing
- **Pricing**: Standard: ~$300/year, EV: ~$700/year
- **Process**: Organization validation required
- **Timeline**: 1-3 business days

### **Alternative Providers:**
- **GlobalSign**: https://www.globalsign.com/code-signing
- **Sectigo**: https://sectigo.com/ssl-certificates/code-signing
- **Comodo**: https://www.comodo.com/business-security/code-signing-certificates.php

## 📝 Application Process

### **Required Information:**
1. **Organization Details**:
   - Legal business name: PT Aventa Intelligent Power
   - Business address
   - Phone number
   - Business registration documents

2. **Technical Contact**:
   - Name and email
   - Phone number

3. **Domain Ownership** (if applicable):
   - Proof of domain ownership

### **Validation Process:**
1. **Organization Check**: Business registration verification
2. **Address Verification**: Physical address confirmation
3. **Phone Verification**: Business phone confirmation
4. **Domain Verification**: WHOIS and DNS checks

## ⚙️ Implementation Steps

### **1. Update Inno Setup Script**
The AventaHFT733.iss has been updated with signing directives:

```ini
; For commercial certificate:
SignTool=signtool sign /fd SHA256 /t http://timestamp.digicert.com /n "PT Aventa Intelligent Power" $f

; For EV certificate:
SignTool=signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /n "PT Aventa Intelligent Power" $f
```

### **2. Certificate Installation**
- Install the certificate in Windows Certificate Store
- Or use PFX file with password protection
- Ensure private key is properly secured

### **3. Signing Process**
1. Build the executable with PyInstaller/Nuitka
2. Sign the executable: `signtool sign /fd SHA256 /t http://timestamp.digicert.com /n "Certificate Name" executable.exe`
3. Build the installer with Inno Setup (signing happens automatically)
4. Verify signatures: `signtool verify /pa executable.exe`

## 🔒 Security Best Practices

### **Private Key Protection:**
- Store private keys on hardware security modules (HSM)
- Use strong passwords for PFX files
- Limit access to signing systems
- Regular backup with encryption

### **Certificate Management:**
- Monitor expiration dates (set calendar reminders)
- Renew certificates 30-60 days before expiration
- Keep certificate revocation lists updated
- Document signing procedures

## 📞 Support Contacts

### **Certificate Authorities:**
- **DigiCert Support**: +1-801-701-9600
- **GlobalSign Support**: +44-1865-643-200

### **Microsoft Signing Requirements:**
- **Authenticode Documentation**: https://docs.microsoft.com/en-us/windows/win32/seccrypto/authenticode
- **Windows Defender Requirements**: https://docs.microsoft.com/en-us/windows/security/threat-protection/windows-defender-application-control/use-app-control-for-business

## ✅ Verification Commands

```batch
# Verify signature
signtool verify /pa /v executable.exe

# Check certificate details
signtool verify /pa /v /d executable.exe

# View certificate in store
certmgr.msc
```

## 📅 Timeline

- **Self-signed**: Ready now (development only)
- **Standard Certificate**: 1-3 business days after application
- **EV Certificate**: 3-5 business days after application

## 💰 Cost Estimate

- **Standard Code Signing**: $200-400/year
- **EV Code Signing**: $500-900/year
- **Additional Costs**: Hardware token (~$50), Express processing (~$100)

---

**Note**: For production distribution, a commercial certificate from a trusted CA is essential to avoid Windows security warnings and ensure user trust.