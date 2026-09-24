import { useCallback, useState } from 'react'

function fallbackCopy(text: string) {
  const ta = document.createElement('textarea')
  ta.value = text
  ta.style.position = 'fixed'
  ta.style.opacity = '0'
  document.body.appendChild(ta)
  ta.select()
  try {
    document.execCommand('copy')
  } catch {
    /* nothing more to try */
  }
  document.body.removeChild(ta)
}

export function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false)

  // `clipboard` is typed as always present and is not: an http origin has none, which is the
  // case the fallback exists for.
  const onClick = useCallback(() => {
    const copy = async () => {
      try {
        if ('clipboard' in navigator) {
          await navigator.clipboard.writeText(text)
        } else {
          fallbackCopy(text)
        }
      } catch {
        fallbackCopy(text)
      }
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    }
    void copy()
  }, [text])

  return (
    <button
      type="button"
      className={copied ? 'copy-btn copied' : 'copy-btn'}
      onClick={onClick}
      aria-label={label}
    >
      <span>{copied ? '✓' : '⧉'}</span>
      <span>{copied ? 'Copied' : 'Copy'}</span>
    </button>
  )
}
