import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { MessageSquare, Send } from 'lucide-react'

import { Avatar, Button, EmptyState } from '@/components/ui'
import { useAuth } from '@/hooks/useAuth'
import { api } from '@/lib/api'
import { formatRelative } from '@/lib/format'

export function ConversationsPage() {
  const { user } = useAuth()
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const { data: conversations, isPending } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => api.conversations.list(),
    refetchInterval: 30_000,
  })

  // Derived rather than synced in an effect: the first thread is the default
  // until the reader picks another one.
  const activeId = selectedId ?? conversations?.[0]?.id ?? null

  return (
    <div className="stack-lg">
      <div className="page-head">
        <h1>Messages</h1>
        <p className="muted">Agree details before you book — and stay in touch during the job.</p>
      </div>

      {isPending ? (
        <div className="skeleton" style={{ height: 220, borderRadius: 'var(--radius-lg)' }} />
      ) : !conversations || conversations.length === 0 ? (
        <EmptyState
          icon={<MessageSquare size={20} />}
          title="No conversations yet"
          description="Message a fundi from their profile to start one."
        />
      ) : (
        <div className="split">
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            {activeId ? (
              <Thread conversationId={activeId} currentUserId={user?.id ?? ''} />
            ) : null}
          </div>

          <aside className="card stack-sm" style={{ padding: 'var(--space-2)' }}>
            {conversations.map((conversation) => {
              const other =
                user?.id === conversation.customer_id
                  ? conversation.fundi_name
                  : conversation.customer_name
              return (
                <button
                  key={conversation.id}
                  className="menu-item"
                  onClick={() => setSelectedId(conversation.id)}
                  style={{
                    background:
                      activeId === conversation.id ? 'var(--surface-sunken)' : undefined,
                  }}
                >
                  <Avatar name={other} size="sm" />
                  <span style={{ minWidth: 0, flex: 1 }}>
                    <strong style={{ display: 'block', fontSize: 'var(--text-sm)' }}>{other}</strong>
                    <span className="subtle" style={{ fontSize: 11 }}>
                      {formatRelative(conversation.last_message_at)}
                    </span>
                  </span>
                </button>
              )
            })}
          </aside>
        </div>
      )}
    </div>
  )
}

function Thread({
  conversationId,
  currentUserId,
}: {
  conversationId: string
  currentUserId: string
}) {
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState('')
  const scroller = useRef<HTMLDivElement>(null)

  const { data: conversation } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => api.conversations.detail(conversationId),
    refetchInterval: 15_000,
  })

  const messages = conversation?.messages ?? []

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight })
  }, [messages.length])

  const send = useMutation({
    mutationFn: (content: string) => api.conversations.send(conversationId, content),
    onSuccess: () => {
      setDraft('')
      void queryClient.invalidateQueries({ queryKey: ['conversation', conversationId] })
      void queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const content = draft.trim()
    if (!content) return
    send.mutate(content)
  }

  return (
    <div className="chat">
      <div className="chat-scroll" ref={scroller}>
        {messages.length === 0 ? (
          <p className="subtle" style={{ textAlign: 'center', padding: 'var(--space-5)' }}>
            No messages yet — say hello.
          </p>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className="bubble"
              data-mine={message.sender_id === currentUserId}
            >
              {message.content}
              <time>{formatRelative(message.created_at)}</time>
            </div>
          ))
        )}
      </div>

      <form className="chat-composer" onSubmit={handleSubmit}>
        <input
          className="input"
          placeholder="Write a message…"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          aria-label="Message"
          maxLength={2000}
        />
        <Button type="submit" variant="primary" disabled={!draft.trim() || send.isPending}>
          <Send size={15} />
          <span className="visually-hidden">Send</span>
        </Button>
      </form>
    </div>
  )
}
