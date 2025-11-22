declare module 'ai/react' {
    import type { FormEvent } from 'react';

    export type ChatMessage = {
        id?: string;
        role: 'user' | 'assistant' | 'system';
        content: string;
    };

    export type UseChatOptions = {
        api?: string;
        body?: Record<string, unknown>;
        initialMessages?: ChatMessage[];
        streamMode?: 'text';
        onFinish?: (message: ChatMessage) => void;
        onError?: (error: unknown) => void;
    };

    export function useChat(options?: UseChatOptions): {
        messages: ChatMessage[];
        input: string;
        handleInputChange: (event: FormEvent<HTMLInputElement>) => void;
        handleSubmit: (event?: FormEvent<HTMLFormElement>) => Promise<void>;
        isLoading: boolean;
        setInput: (value: string) => void;
    };
}
