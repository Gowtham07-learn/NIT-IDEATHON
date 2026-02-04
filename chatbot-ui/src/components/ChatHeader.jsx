function ChatHeader() {
  return (
    <header className="chat-header">
      <div className="header-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
      </div>
      <div>
        <h1>SOP Copilot</h1>
        <p>Administrative AI Assistant</p>
      </div>
    </header>
  )
}

export default ChatHeader
