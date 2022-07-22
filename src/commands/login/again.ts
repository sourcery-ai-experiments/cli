import 'reflect-metadata'

import { storeAccessToken } from '../../auth/config'
import SSOAuth from '../../api/ssoAuth'
import AuthCommand from '../authCommand'

export default class LoginAgain extends AuthCommand {
    static hidden = false
    static description = 'Log in through the DevCycle Universal Login. This will open a browser window.'
    static examples = []

    public async run(): Promise<void> {
        const organization = await this.retrieveOrganizationFromConfig()
        if(!organization) {
            throw(new Error('No saved authorization choices to use'))
        }
        this.token = await this.selectOrganization(organization)
    }
}