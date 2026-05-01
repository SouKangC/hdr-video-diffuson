// Trimmed from Horwitz Academic Project Page Template index.js — only the
// copy-BibTeX and scroll-to-top behaviors are kept; carousel/dropdown/video
// helpers are dropped because this page doesn't use them.

function copyBibTeX() {
  const bibtexElement = document.getElementById('bibtex-code');
  const button = document.querySelector('.copy-bibtex-btn');
  const copyText = button && button.querySelector('.copy-text');
  if (!bibtexElement || !button) return;

  const flashCopied = () => {
    button.classList.add('copied');
    if (copyText) copyText.textContent = 'Copied';
    setTimeout(() => {
      button.classList.remove('copied');
      if (copyText) copyText.textContent = 'Copy';
    }, 2000);
  };

  navigator.clipboard.writeText(bibtexElement.textContent)
    .then(flashCopied)
    .catch((err) => {
      console.error('Failed to copy via Clipboard API, falling back:', err);
      const textArea = document.createElement('textarea');
      textArea.value = bibtexElement.textContent;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      flashCopied();
    });
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

window.addEventListener('scroll', () => {
  const scrollButton = document.querySelector('.scroll-to-top');
  if (!scrollButton) return;
  if (window.pageYOffset > 300) scrollButton.classList.add('visible');
  else scrollButton.classList.remove('visible');
});

// Expose for inline onclick handlers (matches Horwitz template convention).
window.copyBibTeX = copyBibTeX;
window.scrollToTop = scrollToTop;
