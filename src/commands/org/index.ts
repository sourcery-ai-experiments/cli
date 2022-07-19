import {
    Organization,
    fetchOrganizations
} from '../../api/organizations'
import Base from '../base'
import { storeAccessToken } from '../../auth/config'
import SSOAuth from '../../api/ssoAuth'
import { promptForOrganization } from '../../ui/promptForOrganization'
import { fetchProjects } from '../../api/projects'
import { promptForProject } from '../../ui/promptForProject'
import { Flags } from '@oclif/core'
export default class SelectOrganization extends Base {
    static description = 'Select which organization to access through the API'
    static hidden = false
    authRequired = true
    static flags = {
        ...Base.flags,
        'org-id': Flags.string({
            description: 'The id of the org to sign in as',
        }),
        'org-name': Flags.string({
            description: 'The name of the org to sign in as',
        }),
    }

    public async run(): Promise<void> {
        const { flags } = await this.parse(SelectOrganization)
        const selected = await this.retrieveOrganization()
        const token = await this.selectOrganization(selected)

        const projects = await fetchProjects(token)
        if(flags.headless) {
            return this.writer.showResults(projects)
        }
        const selectedProject = await promptForProject(projects)
        await this.updateUserConfig({ project:selectedProject.key })
    }

    private async retrieveOrganization():Promise<Organization> {
        const { flags } = await this.parse(SelectOrganization)
        const organizations = await fetchOrganizations(this.token)
        if (organizations.length === 0) {
            throw('You are not a member of any organizations')
        }
        if(flags['org-id']) {
            const matchingOrg = organizations.find((org) => org.id === flags['org-id'])
            if(!matchingOrg) {
                throw(`You are not a member of an org with the id ${flags['org-id']}`)
            }
            return matchingOrg
        } else if(flags['org-name']) {
            const matchingOrg = organizations.find((org) => org.name === flags['org-name'])
            if(!matchingOrg) {
                throw(`You are not a member of an org with the name ${flags['org-name']}`)
            }
            return matchingOrg
        } else {
            return await promptForOrganization(organizations)
        }
    }

    private async selectOrganization(organization:Organization) {
        const ssoAuth = new SSOAuth()
        const token = await ssoAuth.getAccessToken(organization)
        storeAccessToken(token, this.authPath)
        return token
    }
}