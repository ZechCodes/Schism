const copyIcon = '<svg class="copy-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
const checkIcon = '<svg class="copy-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'

document.addEventListener('DOMContentLoaded', function() {
  // Find all code blocks
  const codeBlocks = document.querySelectorAll('.code-block');
  
  // Add copy button to each code block
  codeBlocks.forEach(function(codeBlock) {
    // Create the button
    const copyButton = document.createElement('button');
    copyButton.className = 'copy-button';
    copyButton.innerHTML = copyIcon + ' Copy';
    
    // Add the button to the code block
    codeBlock.appendChild(copyButton);
    
    // Add click event listener
    copyButton.addEventListener('click', function() {
      // Get the code content
      const codeElement = codeBlock.querySelector('code');
      const codeText = codeElement.textContent;
      
      // Copy to clipboard
      navigator.clipboard.writeText(codeText).then(function() {
        // Success feedback
        copyButton.classList.add('copied');
        copyButton.innerHTML = checkIcon + ' Copied!';
        
        // Reset after 2 seconds
        setTimeout(function() {
          copyButton.classList.remove('copied');
          copyButton.innerHTML = copyIcon + ' Copy';
        }, 2000);
      }).catch(function(err) {
        console.error('Could not copy text: ', err);
        copyButton.textContent = 'Error!';
      });
    });
  });
});
