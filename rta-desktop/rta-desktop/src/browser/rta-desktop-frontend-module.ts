/**
 * Generated using theia-extension-generator
 */
import { RtaDesktopCommandContribution, RtaDesktopMenuContribution } from './rta-desktop-contribution';
import { CommandContribution, MenuContribution } from '@theia/core/lib/common';
import { ContainerModule } from '@theia/core/shared/inversify';

export default new ContainerModule(bind => {
    // add your contribution bindings here
    bind(CommandContribution).to(RtaDesktopCommandContribution);
    bind(MenuContribution).to(RtaDesktopMenuContribution);
});
