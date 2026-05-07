import * as React from 'react';
import { injectable, postConstruct, inject } from '@theia/core/shared/inversify';
import { ReactWidget } from '@theia/core/lib/browser';
import { MessageService } from '@theia/core/lib/common';
import { FileService } from '@theia/filesystem/lib/browser/file-service';
import { URI } from '@theia/core/lib/common/uri';
import { EnvVariablesServer } from '@theia/core/lib/common/env-variables/env-variables-protocol';
import { QuickInputService } from '@theia/core/lib/browser/quick-input/quick-input-service';
import { BinaryBuffer } from '@theia/core/lib/common/buffer';

interface ChatMessage {
    text: string;
    sender: 'user' | 'bot';
}

@injectable()
export class RtaChatWidget extends ReactWidget {

    static readonly ID = 'rta-chat-widget';
    static readonly LABEL = 'RTA AI';
    static readonly DEFAULT_BACKEND_URL = 'https://divisive-herbs-jolly.ngrok-free.dev';

    @inject(MessageService)
    protected readonly messageService!: MessageService;

    @inject(FileService)
    protected readonly fileService!: FileService;

    @inject(EnvVariablesServer)
    protected readonly envVariablesServer!: EnvVariablesServer;

    @inject(QuickInputService)
    protected readonly quickInputService!: QuickInputService;

    protected messages: ChatMessage[] = [
        { text: 'Welcome to RTA AI!', sender: 'bot' }
    ];

    protected apiKey: string | undefined;
    protected backendUrl: string = RtaChatWidget.DEFAULT_BACKEND_URL;
    protected sessionId: string = crypto.randomUUID();
    protected turnIndex: number = 0;

    @postConstruct()
    protected init(): void {
        this.id = RtaChatWidget.ID;
        this.title.label = RtaChatWidget.LABEL;
        this.title.caption = RtaChatWidget.LABEL;
        this.title.closable = false;
        this.title.iconClass = 'fa fa-robot';
        this.update();
        this.loadConfig();
        this.ensureApiKey();
    }

    protected async loadConfig(): Promise<void> {
        try {
            const homeUriStr = await this.envVariablesServer.getHomeDirUri();
            if (homeUriStr) {
                const configUri = new URI(homeUriStr).resolve('.rta/config.json');
                if (await this.fileService.exists(configUri)) {
                    const content = await this.fileService.readFile(configUri);
                    const config = JSON.parse(content.value.toString());
                    if (config.server_url) {
                        this.backendUrl = config.server_url.replace(/\/$/, '');
                    }
                }
            }
        } catch (e) {
            console.error('Error loading config:', e);
        }
    }

    protected async ensureApiKey(): Promise<string | undefined> {
        if (this.apiKey) return this.apiKey;

        // Try load from CLI credentials
        try {
            const homeUriStr = await this.envVariablesServer.getHomeDirUri();
            if (homeUriStr) {
                const credsUri = new URI(homeUriStr).resolve('.rta/credentials');
                if (await this.fileService.exists(credsUri)) {
                    const content = await this.fileService.readFile(credsUri);
                    const text = content.value.toString();
                    const match = text.match(/rta_api_key=(.*)/);
                    if (match && match[1]) {
                        this.apiKey = atob(match[1].trim());
                        return this.apiKey;
                    }
                }
            }
        } catch (e) {
            console.error('Error loading API key:', e);
        }

        // Prompt user
        const key = await this.quickInputService.input({
            prompt: 'Enter your Rta API key',
            placeHolder: 'API key from https://rta-three.vercel.app/dashboard.html'
        });

        if (key) {
            this.apiKey = key;
            await this.saveApiKey(key);
            return key;
        }

        return undefined;
    }

    protected async saveApiKey(key: string): Promise<void> {
        try {
            const homeUriStr = await this.envVariablesServer.getHomeDirUri();
            if (homeUriStr) {
                const rtaDir = new URI(homeUriStr).resolve('.rta');
                if (!(await this.fileService.exists(rtaDir))) {
                    await this.fileService.createFolder(rtaDir);
                }
                const credsUri = rtaDir.resolve('credentials');
                const encoded = btoa(key);
                const content = `rta_api_key=${encoded}\n`;
                await this.fileService.writeFile(credsUri, BinaryBuffer.fromString(content));
            }
        } catch (e) {
            console.error('Error saving API key:', e);
        }
    }

    protected state = {
        inputValue: '',
        isSending: false
    };

    protected async handleSendMessage(text: string): Promise<void> {
        if (!text.trim() || this.state.isSending) return;

        const apiKey = await this.ensureApiKey();
        if (!apiKey) {
            this.messageService.error('RTA API key is required to chat.');
            return;
        }

        this.messages.push({ text, sender: 'user' });
        this.state.isSending = true;
        this.update();

        try {
            const response = await fetch(`${this.backendUrl}/v1/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-KEY': apiKey,
                    'ngrok-skip-browser-warning': '69420'
                },
                body: JSON.stringify({
                    messages: this.messages.map(m => ({
                        role: m.sender === 'user' ? 'user' : 'assistant',
                        content: m.text
                    })),
                    model: 'auto',
                    stream: false,
                    session_id: this.sessionId,
                    turn_index: this.turn_index
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`API Error (${response.status}): ${errorText.substring(0, 100)}`);
            }

            const data = await response.json();
            const reply = data.choices?.[0]?.message?.content || 'No response from RTA.';
            this.messages.push({ text: reply, sender: 'bot' });
            this.turnIndex += 2; // User + Assistant
        } catch (e: any) {
            this.messages.push({ text: `Error: ${e.message}`, sender: 'bot' });
        } finally {
            this.state.isSending = false;
            this.update();
        }
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
                            placeholder={this.state.isSending ? "RTA is thinking..." : "Ask RTA anything..."}
                            style={{
                                flex: 1,
                                padding: '8px 0',
                                backgroundColor: 'transparent',
                                color: 'var(--theia-input-foreground)',
                                border: 'none',
                                outline: 'none',
                                fontSize: 'var(--theia-ui-font-size1)',
                                opacity: this.state.isSending ? 0.5 : 1
                            }} 
                            value={this.state.inputValue}
                            disabled={this.state.isSending}
                            onChange={(e) => {
                                this.state.inputValue = e.target.value;
                                this.update();
                            }}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && this.state.inputValue.trim() && !this.state.isSending) {
                                    this.handleSendMessage(this.state.inputValue);
                                    this.state.inputValue = '';
                                    this.update();
                                }
                            }}
                        />
                        <button 
                            disabled={this.state.isSending || !this.state.inputValue.trim()}
                            onClick={() => {
                                if (this.state.inputValue.trim() && !this.state.isSending) {
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
                                cursor: (this.state.isSending || !this.state.inputValue.trim()) ? 'default' : 'pointer',
                                transition: 'opacity 0.2s',
                                opacity: (this.state.isSending || !this.state.inputValue.trim()) ? 0.3 : 1
                            }}
                        >
                            <i className={this.state.isSending ? "fa fa-spinner fa-spin" : "fa fa-paper-plane"}></i>
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
