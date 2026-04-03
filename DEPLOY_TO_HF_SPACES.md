# 🚀 DEPLOY TO HUGGINGFACE SPACES — STEP-BY-STEP

**Goal**: Get your IncidentResponseEnv live with a public URL  
**Time**: 30 minutes  
**Prerequisites**: HuggingFace account (free)

---

## ✅ STEP 1: Create HuggingFace Space (5 minutes)

### 1.1 Go to HuggingFace Spaces
Visit: https://huggingface.co/spaces

### 1.2 Click "Create new Space"
- **Space name**: `incident-response-env`
- **Space license**: OpenRAIL (or your choice)
- **Select the Space SDK**: `Docker` (NOT Gradio or Streamlit)
- **Visibility**: `Public`

### 1.3 Wait for Space to be created
You'll get a URL like:
```
https://huggingface.co/spaces/YOUR_USERNAME/incident-response-env
```

---

## ✅ STEP 2: Prepare Git Credentials (2 minutes)

### 2.1 Install HuggingFace CLI
```bash
pip install huggingface-hub
```

### 2.2 Login to HuggingFace
```bash
huggingface-cli login
# You'll be prompted for your HF token
# Get one from: https://huggingface.co/settings/tokens
```

---

## ✅ STEP 3: Configure Git Remote (5 minutes)

### 3.1 Open your project directory
```bash
cd /Users/sabaanjum/Documents/Meta\ Hackathon/incident-response-env
```

### 3.2 Add HuggingFace as a git remote
Replace `YOUR_USERNAME` with your actual HuggingFace username:
```bash
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/incident-response-env.git
```

### 3.3 Verify the remote was added
```bash
git remote -v
# Output should show:
# origin  https://github.com/... (if you have one)
# hf      https://huggingface.co/spaces/YOUR_USERNAME/incident-response-env.git
```

---

## ✅ STEP 4: Deploy to HuggingFace Spaces (5 minutes)

### 4.1 Push your code to HF Spaces
```bash
git push hf main
# Or if your branch is 'master':
# git push hf master
```

### 4.2 What happens next:
1. HuggingFace downloads your code
2. Builds Docker image from your Dockerfile
3. Starts container on port 7860
4. Environment becomes accessible at public URL

### 4.3 Monitor the build
Visit your Space page:
```
https://huggingface.co/spaces/YOUR_USERNAME/incident-response-env
```

Look for "Build" tab to see logs. Wait 5-10 minutes for build to complete.

---

## ✅ STEP 5: Get Your Public API URL (2 minutes)

Once deployed, your API is live at:
```
https://YOUR_USERNAME-incident-response-env.hf.space
```

### 5.1 Test the live API
```bash
curl -X POST https://YOUR_USERNAME-incident-response-env.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "single_service_down"}'
```

You should get back a JSON response with the initial state.

### 5.2 Test other endpoints
```bash
# Get available tasks
curl https://YOUR_USERNAME-incident-response-env.hf.space/tasks

# Get health check
curl https://YOUR_USERNAME-incident-response-env.hf.space/health
```

---

## ✅ STEP 6: Update Your Documentation (5 minutes)

### 6.1 Update README.md
Replace the placeholder with your actual username:

Find this line in README.md:
```markdown
[Try IncidentResponseEnv on HuggingFace Spaces →](https://huggingface.co/spaces/YOUR_USERNAME/incident-response-env)
```

Replace `YOUR_USERNAME` with your actual HF username, e.g.:
```markdown
[Try IncidentResponseEnv on HuggingFace Spaces →](https://huggingface.co/spaces/sabaanjum/incident-response-env)
```

### 6.2 Test the live demo link
Click it and verify it opens your HF Space.

### 6.3 Add API endpoint to documentation
Add to README.md:
```markdown
## 🌐 API Endpoint

Live API: `https://YOUR_USERNAME-incident-response-env.hf.space`

Example:
```bash
curl -X POST https://YOUR_USERNAME-incident-response-env.hf.space/reset \
  -d '{"task_id": "single_service_down"}'
```

---

## ✅ STEP 7: Create Demo Usage Instructions (Optional)

Add this to your HF Space README:

```markdown
# Try It Now

## Via API
```bash
# Start an incident
curl -X POST https://YOUR_USERNAME-incident-response-env.hf.space/reset \
  -d '{"task_id": "single_service_down"}'

# Investigate
curl -X POST https://YOUR_USERNAME-incident-response-env.hf.space/step \
  -d '{"action_type": "investigate", "target": "payment-service"}'

# Diagnose
curl -X POST https://YOUR_USERNAME-incident-response-env.hf.space/step \
  -d '{"action_type": "diagnose", "target": "OutOfMemoryError"}'

# Fix
curl -X POST https://YOUR_USERNAME-incident-response-env.hf.space/step \
  -d '{"action_type": "fix", "target": "payment-service"}'
```

## Via Python Client
```python
import requests

api_url = "https://YOUR_USERNAME-incident-response-env.hf.space"

# Reset
response = requests.post(f"{api_url}/reset", json={"task_id": "single_service_down"})
print(response.json())
```

---

## 🐛 TROUBLESHOOTING

### **Build Failed**
1. Check the Build logs on HF Space page
2. Common issues:
   - Dockerfile syntax error → Fix and push again
   - Missing requirements → Add to requirements.txt
   - Port mismatch → Ensure Dockerfile uses port 7860

### **API Timeout**
1. Space might still be building (wait 10 min)
2. Or port might be wrong (check Dockerfile)
3. Or dependencies might not be installed (check logs)

### **Can't connect to API**
```bash
# Verify space is running
curl https://YOUR_USERNAME-incident-response-env.hf.space/health

# Should return:
# {"status": "ok"}
```

### **Need to update code**
```bash
# Make changes locally
# Commit
git add .
git commit -m "Fix bug"

# Push to HF
git push hf main

# Build will restart automatically
```

---

## ✅ VERIFICATION CHECKLIST

- [ ] HF Space created
- [ ] Git remote added
- [ ] Code pushed to HF (`git push hf main`)
- [ ] Build completed (check logs)
- [ ] Can curl `/health` endpoint
- [ ] Can curl `/reset` endpoint
- [ ] README updated with live link
- [ ] Demo link works

---

## 🎉 YOU'RE LIVE!

Your IncidentResponseEnv is now publicly accessible!

### Share with judges:
```
GitHub: https://github.com/YOUR_USERNAME/incident-response-env
Live Demo: https://huggingface.co/spaces/YOUR_USERNAME/incident-response-env
API: https://YOUR_USERNAME-incident-response-env.hf.space
```

---

## 📞 NEXT STEPS

1. ✅ Deployment complete
2. ⏳ [Update documentation](HACKATHON_SUBMISSION_ROADMAP.md#phase-3-documentation)
3. ⏳ [Prepare GitHub submission](HACKATHON_SUBMISSION_ROADMAP.md#phase-4-github-submission)
4. ⏳ [Optional: Record demo video](HACKATHON_SUBMISSION_ROADMAP.md#phase-5-demo-optional-but-impressive)
5. ⏳ [Submit to hackathon](HACKATHON_SUBMISSION_ROADMAP.md)

Congratulations! 🚀
