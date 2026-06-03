import React from 'react';

export interface MessageProps {
  id: string;
  content: string;
  sender_type: 'customer' | 'agent' | 'ai';
  created_at?: string;
}

export const MessageBubble: React.FC<{ message: MessageProps }> = React.memo(({ message }) => {
  const isCustomer = message.sender_type === 'customer';
  
  return (
    <div className={`flex w-full ${isCustomer ? 'justify-end' : 'justify-start'} mb-6 group`}>
      <div 
        className={`max-w-[75%] px-5 py-3.5 rounded-2xl border backdrop-blur-md transition-all duration-300 ease-out ${
          isCustomer 
            ? 'bg-white/5 border-white/10 text-primary-text rounded-br-sm' 
            : 'bg-accent-blue/10 border-accent-blue/20 text-accent-blue rounded-bl-sm shadow-[0_4px_20px_-5px_rgba(56,189,248,0.15)]'
        }`}
      >
        <div className={`text-sm leading-relaxed ${isCustomer ? 'font-normal' : 'font-medium tracking-wide'}`}>
          {message.content}
        </div>
        {message.created_at && (
          <div className={`text-[10px] mt-2 tracking-wider uppercase opacity-50 ${isCustomer ? 'text-secondary-text' : 'text-accent-blue'} group-hover:opacity-100 transition-opacity duration-300`}>
            {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>
    </div>
  );
});

MessageBubble.displayName = 'MessageBubble';
