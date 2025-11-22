import type { ReactNode } from 'react';
import { Badge } from '../ui/badge';

function cn(...classes: Array<string | undefined>): string {
    return classes.filter(Boolean).join(' ');
}

type ChatMessageProps = {
    role: 'user' | 'assistant';
    content: ReactNode;
    tone?: 'neutral' | 'action' | 'warning';
};

export function ChatMessage({
    role,
    content,
    tone = 'neutral'
}: ChatMessageProps): JSX.Element {
    const roleLabel = role === 'assistant' ? 'AI応答' : 'リクエスト';
    const toneBadge = {
        neutral: null,
        action: <Badge variant="accent">次のアクション提案</Badge>,
        warning: <Badge variant="warning">注意</Badge>
    }[tone];

    return (
        <div
            className={cn(
                'chat-message',
                role === 'assistant' ? 'chat-message--assistant' : undefined
            )}
        >
            <div className="chat-message__role">{roleLabel}</div>
            <div>{content}</div>
            {toneBadge}
        </div>
    );
}
