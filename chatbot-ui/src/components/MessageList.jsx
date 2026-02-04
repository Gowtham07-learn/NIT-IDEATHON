function MessageList({ messages, isLoading }) {
  const formatContent = (text) => {
    return text.split('\n').map((line, i) => {
      if (line.startsWith('**') && line.endsWith('**')) {
        return <strong key={i}>{line.slice(2, -2)}</strong>
      }
      if (line.startsWith('- ') || line.startsWith('• ')) {
        return <li key={i}>{line.slice(2)}</li>
      }
      if (/^\d+\.\s/.test(line)) {
        return <li key={i}>{line.replace(/^\d+\.\s/, '')}</li>
      }
      if (line.startsWith('#')) {
        const level = line.match(/^#+/)[0].length
        const content = line.replace(/^#+\s*/, '')
        const Tag = `h${Math.min(level, 4)}`
        return <Tag key={i}>{content}</Tag>
      }
      return <p key={i}>{line || <br />}</p>
    })
  }

  return (
    <main className="message-list">
      {messages.map((msg) => (
        <div key={msg.id} className={`message message-${msg.role}`}>
          <div className="message-avatar">
            {msg.role === 'user' ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="12" cy="7" r="4" />
              </svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="10" rx="2" ry="2" />
                <circle cx="12" cy="5" r="3" />
                <path d="M12 8v3" />
                <line x1="8" y1="16" x2="16" y2="16" />
              </svg>
            )}
          </div>
          <div className="message-content">
            {msg.image && (
              <img src={msg.image} alt="Uploaded screenshot" className="msg-screenshot" />
            )}
            <div className="message-text">{formatContent(msg.content)}</div>
          </div>
        </div>
      ))}
      {isLoading && (
        <div className="message message-assistant">
          <div className="message-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="10" rx="2" ry="2" />
              <circle cx="12" cy="5" r="3" />
              <path d="M12 8v3" />
              <line x1="8" y1="16" x2="16" y2="16" />
            </svg>
          </div>
          <div className="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      )}
    </main>
  )
}

export default MessageList
