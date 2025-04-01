document.addEventListener('DOMContentLoaded', function() {
  // Theme variables
  const DARK_THEME = 'dark';
  const LIGHT_THEME = 'light';
  const THEME_STORAGE_KEY = 'schism-theme-preference';
  
  // Create theme toggle button
  const createToggleButton = () => {
    const header = document.querySelector('header .container');
    const toggleContainer = document.createElement('div');
    toggleContainer.className = 'theme-toggle-container';
    
    const toggleButton = document.createElement('button');
    toggleButton.className = 'theme-toggle';
    toggleButton.setAttribute('aria-label', 'Toggle dark/light mode');
    toggleButton.innerHTML = `
      <svg class="sun-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </svg>
      <svg class="moon-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>
    `;
    
    toggleContainer.appendChild(toggleButton);
    header.appendChild(toggleContainer);
    
    return toggleButton;
  };
  
  // Get saved theme from localStorage or use system preference
  const getSavedTheme = () => {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    if (savedTheme) {
      return savedTheme;
    }
    
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return DARK_THEME;
    }
    
    return LIGHT_THEME;
  };
  
  // Apply theme to document
  const applyTheme = (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  };
  
  // Toggle between themes
  const toggleTheme = () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === DARK_THEME ? LIGHT_THEME : DARK_THEME;
    applyTheme(newTheme);
  };
  
  // Initialize theme
  const initTheme = () => {
    const savedTheme = getSavedTheme();
    applyTheme(savedTheme);
    
    const toggleButton = createToggleButton();
    toggleButton.addEventListener('click', toggleTheme);
  };
  
  // Start the theme system
  initTheme();
});
