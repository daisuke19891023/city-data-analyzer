import type { FormEvent } from 'react';

export function useChat(): {
    messages: Array<{ id?: string; role: 'assistant' | 'user'; content: string }>;
    input: string;
    handleInputChange: (event: FormEvent<HTMLInputElement>) => void;
    handleSubmit: (event?: FormEvent<HTMLFormElement>) => Promise<void>;
    isLoading: boolean;
    setInput: (value: string) => void;
} {
    return {
        messages: [],
        input: '',
        handleInputChange: () => undefined,
        handleSubmit: async () => undefined,
        isLoading: false,
        setInput: () => undefined
    };
}
