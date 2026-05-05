/**
 * Generated using theia-extension-generator
 */
import { RtaDesktopCommandContribution, RtaDesktopMenuContribution } from './rta-desktop-contribution';
import { CommandContribution, MenuContribution } from '@theia/core/lib/common';
import { ContainerModule } from '@theia/core/shared/inversify';
import { RtaChatWidget } from './rta-chat-widget';
import { RtaChatContribution } from './rta-chat-contribution';
import { WidgetFactory, FrontendApplicationContribution, bindViewContribution } from '@theia/core/lib/browser';

export default new ContainerModule(bind => {
    // add your contribution bindings here
    bind(CommandContribution).to(RtaDesktopCommandContribution);
    bind(MenuContribution).to(RtaDesktopMenuContribution);

    bindViewContribution(bind, RtaChatContribution);
    bind(FrontendApplicationContribution).toDynamicValue(ctx => ctx.container.get(RtaChatContribution));
    bind(RtaChatWidget).toSelf();
    bind(WidgetFactory).toDynamicValue(ctx => ({
        id: RtaChatWidget.ID,
        createWidget: () => ctx.container.get<RtaChatWidget>(RtaChatWidget)
    }));
});
