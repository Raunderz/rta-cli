import * as React from 'react';
import { injectable, postConstruct, inject } from '@theia/core/shared/inversify';
import { ReactWidget } from '@theia/core/lib/browser';
import { MessageService } from '@theia/core/lib/common';

interface ChatMessage {
    text: string;
    sender: 'user' | 'bot';
}

@injectable()
export class RtaChatWidget extends ReactWidget {

    static readonly ID = 'rta-chat-widget';
    static readonly LABEL = 'RTA Chat';

    @inject(MessageService)
    protected readonly messageService!: MessageService;

    protected messages: ChatMessage[] = [
        { text: 'Welcome to RTA Chat!', sender: 'bot' }
    ];

    @postConstruct()
    protected init(): void {
        this.id = RtaChatWidget.ID;
        this.title.label = RtaChatWidget.LABEL;
        this.title.caption = RtaChatWidget.LABEL;
        this.title.closable = false;
        this.title.iconClass = 'fa fa-comments';
        this.update();
    }

    protected handleSendMessage(text: string): void {
        if (!text.trim()) return;

        this.messages.push({ text, sender: 'user' });
        this.update();

        // Simulate bot reply
        setTimeout(() => {
            this.messages.push({ text: 'This feature is currently under construction. Stay tuned!', sender: 'bot' });
            this.update();
        }, 500);
    }

    protected render(): React.ReactNode {
        return (
            <div id="rta-chat-container" style={{
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                backgroundColor: 'var(--theia-layout-color1)',
                color: 'var(--theia-ui-font-color1)',
                fontSize: 'var(--theia-ui-font-size1)'
            }}>
                <div style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px'
                }}>
                    {this.messages.map((m, i) => (
                        <div key={i} style={{
                            alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
                            backgroundColor: m.sender === 'user' ? 'var(--theia-brand-color1)' : 'var(--theia-layout-color3)',
                            color: m.sender === 'user' ? 'white' : 'inherit',
                            padding: '8px 12px',
                            borderRadius: '12px',
                            borderBottomRightRadius: m.sender === 'user' ? '2px' : '12px',
                            borderBottomLeftRadius: m.sender === 'bot' ? '2px' : '12px',
                            maxWidth: '85%',
                            boxShadow: '0 1px 2px rgba(0,0,0,0.1)',
                            wordBreak: 'break-word'
                        }}>
                            {m.text}
                        </div>
                    ))}
                </div>
                
                <div style={{
                    padding: '12px',
                    borderTop: '1px solid var(--theia-border-color)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                }}>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <input 
                            type="text" 
                            placeholder="Type a message..." 
                            style={{
                                flex: 1,
                                padding: '8px 12px',
                                backgroundColor: 'var(--theia-input-background)',
                                color: 'var(--theia-input-foreground)',
                                border: '1px solid var(--theia-input-border)',
                                borderRadius: '20px',
                                outline: 'none'
                            }} 
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    const input = e.target as HTMLInputElement;
                                    this.handleSendMessage(input.value);
                                    input.value = '';
                                }
                            }}
                        />
                        <button 
                            onClick={() => {
                                const input = document.querySelector('#rta-chat-container input') as HTMLInputElement;
                                this.handleSendMessage(input.value);
                                input.value = '';
                            }}
                            style={{
                                padding: '8px 16px',
                                backgroundColor: 'var(--theia-button-background)',
                                color: 'var(--theia-button-foreground)',
                                border: 'none',
                                borderRadius: '20px',
                                cursor: 'pointer',
                                fontWeight: 'bold'
                            }}
                        >
                            Send
                        </button>
                    </div>
                    <div style={{ fontSize: '10px', opacity: 0.6, textAlign: 'center' }}>
                        RTA AI - Experimental
                    </div>
                </div>
            </div>
        );
    }
}
