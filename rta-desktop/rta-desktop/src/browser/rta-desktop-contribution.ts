import { injectable } from '@theia/core/shared/inversify';
import { Command, CommandContribution, CommandRegistry, MenuContribution, MenuModelRegistry, MessageService } from '@theia/core/lib/common';
import { CommonMenus } from '@theia/core/lib/browser';

export const RtaDesktopCommand: Command = {
    id: 'rta-desktop.command',
    label: 'Say Hello',
};

@injectable()
export class RtaDesktopCommandContribution implements CommandContribution {

    constructor(
        protected readonly messageService: MessageService,
    ) { }

    registerCommands(commands: CommandRegistry): void {
        commands.registerCommand(RtaDesktopCommand, {
            execute: () => this.messageService.info('Hello World!')
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
