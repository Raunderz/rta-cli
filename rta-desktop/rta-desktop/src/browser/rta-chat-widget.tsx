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
    static readonly LABEL = 'RTA AI';

    @inject(MessageService)
    protected readonly messageService!: MessageService;

    protected messages: ChatMessage[] = [
        { text: 'Welcome to RTA AI!', sender: 'bot' }
    ];

    @postConstruct()
    protected init(): void {
        this.id = RtaChatWidget.ID;
        this.title.label = RtaChatWidget.LABEL;
        this.title.caption = RtaChatWidget.LABEL;
        this.title.closable = false;
        this.title.iconClass = 'fa fa-robot';
        this.update();
    }

    protected state = {
        inputValue: ''
    };

    protected handleSendMessage(text: string): void {
        if (!text.trim()) return;

        this.messages.push({ text, sender: 'user' });
        this.update();

        // Simulate bot reply
        setTimeout(() => {
            const reply = this.getMockReply(text);
            this.messages.push({ text: reply, sender: 'bot' });
            this.update();
        }, 1000);
    }

    protected getMockReply(userText: string): string {
        const lower = userText.toLowerCase();
        if (lower.includes('hello') || lower.includes('hi')) return 'Hello! How can I help you today?';
        if (lower.includes('help')) return 'I can help you navigate the RTA desktop application. What do you need?';
        return `I received your message: "${userText}". This is a sample reply from RTA AI.`;
    }

    protected render(): React.ReactNode {
        return (
            <div id="rta-chat-container" style={{
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                backgroundColor: 'var(--theia-layout-color1)',
                color: 'var(--theia-ui-font-color1)',
                fontFamily: 'var(--theia-ui-font-family)',
                fontSize: 'var(--theia-ui-font-size1)'
            }}>
                <div style={{
                    padding: '16px',
                    borderBottom: '1px solid var(--theia-border-color)',
                    fontWeight: 'bold',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}>
                    <i className="fa fa-robot" style={{ color: 'var(--theia-brand-color1)' }}></i>
                    RTA AI Assistant
                </div>

                <div style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '16px'
                }}>
                    {this.messages.map((m, i) => (
                        <div key={i} style={{
                            alignSelf: m.sender === 'user' ? 'flex-end' : 'flex-start',
                            backgroundColor: m.sender === 'user' ? '#007acc' : '#3c3c3c',
                            color: 'white',
                            padding: '10px 14px',
                            borderRadius: '16px',
                            border: '1px solid ' + (m.sender === 'user' ? '#005a9e' : '#555'),
                            borderBottomRightRadius: m.sender === 'user' ? '2px' : '16px',
                            borderBottomLeftRadius: m.sender === 'bot' ? '2px' : '16px',
                            maxWidth: '80%',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                            wordBreak: 'break-word',
                            lineHeight: '1.4'
                        }}>
                            {m.text}
                        </div>
                    ))}
                </div>
                
                <div style={{
                    padding: '16px',
                    borderTop: '1px solid var(--theia-border-color)',
                    backgroundColor: 'var(--theia-layout-color2)'
                }}>
                    <div style={{ 
                        display: 'flex', 
                        gap: '10px',
                        backgroundColor: 'var(--theia-input-background)',
                        border: '1px solid var(--theia-input-border)',
                        borderRadius: '24px',
                        padding: '4px 4px 4px 16px',
                        alignItems: 'center'
                    }}>
                        <input 
                            type="text" 
                            placeholder="Ask RTA anything..." 
                            style={{
                                flex: 1,
                                padding: '8px 0',
                                backgroundColor: 'transparent',
                                color: 'var(--theia-input-foreground)',
                                border: 'none',
                                outline: 'none',
                                fontSize: 'var(--theia-ui-font-size1)'
                            }} 
                            value={this.state.inputValue}
                            onChange={(e) => {
                                this.state.inputValue = e.target.value;
                                this.update();
                            }}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && this.state.inputValue.trim()) {
                                    this.handleSendMessage(this.state.inputValue);
                                    this.state.inputValue = '';
                                    this.update();
                                }
                            }}
                        />
                        <button 
                            onClick={() => {
                                if (this.state.inputValue.trim()) {
                                    this.handleSendMessage(this.state.inputValue);
                                    this.state.inputValue = '';
                                    this.update();
                                }
                            }}
                            style={{
                                width: '32px',
                                height: '32px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                backgroundColor: 'var(--theia-brand-color1)',
                                color: 'white',
                                border: 'none',
                                borderRadius: '50%',
                                cursor: 'pointer',
                                transition: 'opacity 0.2s'
                            }}
                        >
                            <i className="fa fa-paper-plane"></i>
                        </button>
                    </div>
                    <div style={{ 
                        fontSize: '10px', 
                        marginTop: '8px',
                        opacity: 0.5, 
                        textAlign: 'center',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                    }}>
                        Powered by RTA Intelligence
                    </div>
                </div>
            </div>
        );
    }
}
