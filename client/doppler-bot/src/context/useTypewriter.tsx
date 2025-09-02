import { useState, useEffect, useRef } from 'react';

const useTypewriter = (text: string | undefined, options: {
    typingSpeed?: number;
    startDelay?: number;
    endDelay?: number;
} = {}) => {
    const {
        typingSpeed = 30, // milliseconds per character
        startDelay = 0,   // delay before starting to type
        endDelay = 0
    } = options;

    const [displayedText, setDisplayedText] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const textQueue = useRef<string[]>([]);
    const currentIndex = useRef(0);
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);

    // Clear any existing timeout on component unmount
    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

    // Handle text changes
    useEffect(() => {
        if (text === displayedText || text === undefined) return;

        // If currently typing, queue the new text
        if (isTyping) {
            // if (textQueue.current[textQueue.current.length - 1] !== text) textQueue.current.push(text);
            return;
        }

        // Start typing the new text
        const startTyping = (nextText?: string) => {
            setIsTyping(true);
            currentIndex.current = -1; // Start from -1 so first increment gets first character
            setDisplayedText('');

            const typeNextChar = () => {
                currentIndex.current++; // Increment first
                if (currentIndex.current < text.length) {
                    setDisplayedText(text.slice(0, currentIndex.current + 1));
                    timeoutRef.current = setTimeout(typeNextChar, typingSpeed);
                } else {
                    setTimeout(() => {
                        setIsTyping(false);
                        if (textQueue.current.length > 0) {
                            const nextText = textQueue.current.shift();
                            startTyping(nextText);
                        }
                    }, endDelay);
                }
            };

            // Start typing after the specified delay
            timeoutRef.current = setTimeout(typeNextChar, startDelay);
        };

        startTyping(text);
    }, [text, typingSpeed, startDelay]);

    return {
        displayedText,
        isTyping,
        cursor: isTyping ? '|' : '',
        hasQueuedText: textQueue.current.length > 0
    };
};

export default useTypewriter; 