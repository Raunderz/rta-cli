import { injectable, inject } from '@theia/core/shared/inversify';
import { FrontendApplicationContribution, FrontendApplication, StatusBar, StatusBarAlignment } from '@theia/core/lib/browser';
import { EnvVariablesServer } from '@theia/core/lib/common/env-variables/env-variables-protocol';
import { FileService } from '@theia/filesystem/lib/browser/file-service';
import { URI } from '@theia/core/lib/common/uri';

@injectable()
export class RtaStatusContribution implements FrontendApplicationContribution {

    @inject(StatusBar)
    protected readonly statusBar: StatusBar;

    @inject(EnvVariablesServer)
    protected readonly envVariablesServer: EnvVariablesServer;

    @inject(FileService)
    protected readonly fileService: FileService;

    protected backendUrl: string = 'https://divisive-herbs-jolly.ngrok-free.dev';

    async onStart(app: FrontendApplication): Promise<void> {
        await this.loadConfig();
        this.updateStatus();
        setInterval(() => this.updateStatus(), 300000); // Check every 5 minutes
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
            console.error('Error loading config in status bar:', e);
        }
    }

    protected async updateStatus(): Promise<void> {
        let isOnline = false;
        try {
            const res = await fetch(`${this.backendUrl}/v1/status`, { 
                headers: { "ngrok-skip-browser-warning": "true" } 
            });
            if (res.ok) {
                const data = await res.json();
                isOnline = data.status === 'operational';
            }
        } catch (e) {
            isOnline = false;
        }

        this.statusBar.setElement('rta-status', {
            text: `${isOnline ? '$(check)' : '$(x)'} Rta: ${isOnline ? 'Online' : 'Offline'}`,
            alignment: StatusBarAlignment.RIGHT,
            priority: 100,
            color: isOnline ? 'var(--theia-debugIcon-breakpointForeground)' : 'var(--theia-errorForeground)',
            tooltip: `Rta Server Status: ${isOnline ? 'Operational' : 'Disconnected'}`,
            command: 'rta-chat:toggle'
        });
    }
}
