'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';

// Define the shape of the context state
interface SocketContextState {
  socket: Socket | null;
  isConnected: boolean;
}

// Create the context with a default value
const SocketContext = createContext<SocketContextState>({
  socket: null,
  isConnected: false,
});

// Create a custom hook for easy access to the context
export const useSocket = () => {
  return useContext(SocketContext);
};

// Define the props for the provider component
interface SocketProviderProps {
  children: ReactNode;
}

// Create the SocketProvider component
export const SocketProvider = ({ children }: SocketProviderProps) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect to the Socket.IO server
    // Replace this with your actual server URL
    const socketInstance = io(process.env.NEXT_PUBLIC_SOCKET_URL || 'https://dopplertrading.com', {
      transports: ['websocket', 'polling'],
      upgrade: true,
      rememberUpgrade: true,
      timeout: 20000,
      forceNew: true
    });
    // const socketInstance = io('http://localhost:5000');

    socketInstance.on('connect', () => {
      console.log('Socket connected:', socketInstance.id);
      setIsConnected(true);
    });

    socketInstance.on('disconnect', () => {
      console.log('Socket disconnected');
      setIsConnected(false);
    });

    setSocket(socketInstance);

    // Clean up the connection when the component unmounts
    return () => {
      socketInstance.disconnect();
    };
  }, []);

  return (
    <SocketContext.Provider value={{ socket, isConnected }}>
      {children}
    </SocketContext.Provider>
  );
}; 