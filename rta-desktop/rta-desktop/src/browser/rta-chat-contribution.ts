import { injectable } from '@theia/core/shared/inversify';
import { AbstractViewContribution } from '@theia/core/lib/browser';
import { RtaChatWidget } from './rta-chat-widget';
import { Command, CommandRegistry, MenuModelRegistry } from '@theia/core/lib/common';
import { CommonMenus, FrontendApplication } from '@theia/core/lib/browser';

export const RtaChatCommand: Command = {
    id: 'rta-chat:toggle',
    label: 'Toggle RTA Chat',
};

@injectable()
export class RtaChatContribution extends AbstractViewContribution<RtaChatWidget> {

    constructor() {
        super({
            widgetId: RtaChatWidget.ID,
            widgetName: RtaChatWidget.LABEL,
            defaultWidgetOptions: {
                area: 'right'
            },
            toggleCommandId: RtaChatCommand.id
        });
    }

    async onStart(app: FrontendApplication): Promise<void> {
        await this.openView({ reveal: true });
    }

    registerCommands(commands: CommandRegistry): void {
        super.registerCommands(commands);
    }

    registerMenus(menus: MenuModelRegistry): void {
        super.registerMenus(menus);
        menus.registerMenuAction(CommonMenus.VIEW_VIEWS, {
            commandId: RtaChatCommand.id,
            label: RtaChatWidget.LABEL
        });
    }
}
