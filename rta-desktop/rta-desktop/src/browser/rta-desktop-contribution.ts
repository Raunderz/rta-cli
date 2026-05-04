import { injectable, inject } from '@theia/core/shared/inversify';
import { Command, CommandContribution, CommandRegistry, MenuContribution, MenuModelRegistry, MessageService } from '@theia/core/lib/common';
import { CommonMenus, FrontendApplicationContribution, FrontendApplication } from '@theia/core/lib/browser';

export const RtaDesktopCommand: Command = {
    id: 'RtaDesktop.command',
    label: 'Rta: Show Info'
};

@injectable()
export class RtaDesktopCommandContribution implements CommandContribution {
    
    @inject(MessageService)
    protected readonly messageService!: MessageService;

    registerCommands(registry: CommandRegistry): void {
        registry.registerCommand(RtaDesktopCommand, {
            execute: () => this.messageService.info('Rta Desktop - Real-Time Assistant')
        });
    }
}

@injectable()
export class RtaDesktopMenuContribution implements MenuContribution {

    registerMenus(menus: MenuModelRegistry): void {
        menus.registerMenuAction(CommonMenus.EDIT_FIND, {
            commandId: RtaDesktopCommand.id,
            label: RtaDesktopCommand.label
        });
    }
}

@injectable()
export class RtaBrandingContribution implements FrontendApplicationContribution {
    onStart(app: FrontendApplication): void {
        app.setTitle('Rta');
    }
}
