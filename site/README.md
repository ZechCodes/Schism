# Schism Landing Page

This is the landing page for the [Schism](https://github.com/ZechCodes/Schism) project, a service framework for Python that makes modularity simple.

## Directory Structure

```
site/
├── css/
│   ├── styles.css          # Main stylesheet
│   └── syntax-highlight.css # Code syntax highlighting styles
├── js/
│   ├── copy-code.js        # Code copy button functionality
│   └── theme-toggle.js     # Dark/light theme toggle
├── favicon.svg             # Site favicon
├── index.html              # Main landing page
└── README.md               # This file
```

## Features

- Responsive design that works on mobile and desktop
- Dark/light theme toggle with localStorage persistence
- Syntax highlighting for code examples
- Copy-to-clipboard functionality for code blocks
- Animated theme toggle icon

## Setup for GitHub Pages

1. In your GitHub repository, go to Settings > Pages
2. Under "Source", select the branch where these files are located (usually `main` or `gh-pages`)
3. Select the `/site` folder as the publishing source
4. Click Save

GitHub will then publish your site at `https://zechcodes.github.io/Schism/`

## Local Development

To test this landing page locally, you can use Python's built-in HTTP server:

```bash
cd site
python -m http.server
```

Then open your browser to `http://localhost:8000`
