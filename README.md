---
title: Mayank Portfolio
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: streamlit
app_file: projects/template-streamlit-app/app.py
pinned: false
license: mit
---

# Mayank Goyal – AI PM Portfolio
This is my interactive portfolio hosted on Hugging Face Spaces.


# AI PM Portfolio Scaffold

This repo is a **ready-to-host** scaffold for your AI Product Manager portfolio.
It includes:
- A **Streamlit app** template that's deployable to **Hugging Face Spaces** out of the box
- A minimal static **portfolio site** (website/) you can publish with GitHub Pages (or host on Vercel/Netlify)
- A starter **AI Travel Planner** app structure to extend

## Quick Start

### 1) Create a new GitHub repository
- Name it something like `mayank-ai-portfolio`
- Push the contents of this scaffold

### 2) Deploy the Streamlit demo to Hugging Face Spaces
- Create a new Space at https://huggingface.co/new-space
- Space type: **Streamlit**
- Select **From Git** and connect this repo
- Set the Space SDK to **streamlit** and the `app_file` to `projects/template-streamlit-app/app.py`
- The app will build automatically from `requirements.txt`

### 3) Publish your portfolio site
- If using GitHub Pages: set Pages source to `/website` (root) on **main** or use `/ (root)` pointing to website folder
- If using Vercel/Netlify: point to `website/`

### 4) Add more projects
- Copy `projects/template-streamlit-app` to `projects/<your-project>` and customize
- Or continue building out `projects/ai-travel-planner`

## Structure
```
.
├── projects
│   ├── ai-travel-planner
│   │   ├── app.py                  # (empty starter placeholder)
│   │   ├── requirements.txt        # add your libs here
│   │   ├── planner/                # prompts, agent logic
│   │   ├── retrieval/              # POI APIs, vector index
│   │   ├── routing/                # OR-Tools, distance matrix
│   │   ├── data/                   # cache/db
│   │   └── tests/                  # eval suite
│   └── template-streamlit-app
│       ├── app.py
│       ├── requirements.txt
│       └── README.md
└── website
    ├── index.html
    └── style.css
```

## FAQ

**Why Hugging Face Spaces?** Free-ish, zero DevOps, perfect for PM demos.  
**Can I embed the app on my site?** Yes, use an `<iframe>` to embed the Space into `website/index.html`.  
**Private keys?** Use HF Space **Secrets** (Settings → Variables) for API keys. Never commit keys.
