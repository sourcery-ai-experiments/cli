import Base from '../base'
import { storeAccessToken } from '../../auth/config'
import SSOAuth from '../../api/ssoAuth'
import { fetchOrganizations, Organization } from '../../api/organizations'
import { promptForOrganization } from '../../ui/promptForOrganization'
import { fetchProjects, Project } from '../../api/projects'
import { promptForProject } from '../../ui/promptForProject'
import { togglebot } from '../../ui/togglebot'
import { showResults, successMessage } from '../../ui/output'
import { Flags } from '@oclif/core'

export default class Login extends Base {
    static hidden = false
    static description = 'Log in through the DevCycle Universal Login. This will open a browser window. The user will be prompted to select an organization and project after initial login.'

    static examples = []
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
        const { flags } = await this.parse(Login)
        const ssoAuth = new SSOAuth()
        this.token = await ssoAuth.getAccessToken()
        storeAccessToken(this.token, this.authPath)

        if (flags.headless) {
            return this.runHeadless()
        } else {
            return this.runInteractive()
        }
    }

    private async runHeadless(): Promise<void> {
        const organizations = await fetchOrganizations(this.token)
        const filteredOrgs = organizations.map(({id,display_name,name}) => {
            return {id,display_name,name}
        })
        const organization = await this.organizationFromFlags(organizations)
        if(organization === null) {
            return showResults({organizations: filteredOrgs})
        }
        //await new Promise(resolve => setTimeout(resolve, 5000))
        await this.selectOrganization(organization)
        const projects = await fetchProjects(this.token)
        const project = await this.projectFromFlags(projects)
        if(project === null) {
            return showResults({projects})
        }
    }

    private async runInteractive(): Promise<void> {
        const organizations = await fetchOrganizations(this.token)
        if (organizations.length === 0) {
            throw('You are not a member of any organizations')
        }
        const flagOrganization = await this.organizationFromFlags(organizations)
        const selectedOrg = flagOrganization || await promptForOrganization(organizations)
        await this.selectOrganization(selectedOrg)

        const projects = await fetchProjects(this.token)
        const flagProject = await this.projectFromFlags(projects)
        const selectedProject = flagProject || await promptForProject(projects)
        successMessage(`Selected project ${selectedProject.key}`)
        await this.updateUserConfig({ project: selectedProject.key })

        console.log('')
        successMessage('Successfully logged in to DevCycle')
        console.log('')
        console.log(togglebot)
    }

    private async organizationFromFlags(organizations:Organization[]): Promise<(Organization | null)> {
        const { flags } = await this.parse(Login)
        if(flags['org-id']) {
            const matchingOrg = organizations.find((org) => org.id === flags['org-id'])
            if(!matchingOrg) {
                console.error(`You are not a member of an org with the id ${flags['org-id']}`)
                throw(`You are not a member of an org with the id ${flags['org-id']}`)
            }
            return matchingOrg
        } else if(flags['org-name']) {
            const matchingOrg = organizations.find((org) => org.name === flags['org-name'])
            if(!matchingOrg) {
                throw(`You are not a member of an org with the name ${flags['org-name']}`)
            }
            return matchingOrg
        }
        return null
    }

    private async projectFromFlags(projects:Project[]): Promise<Project | null> {
        const { flags } = await this.parse(Login)
        if(flags.project) {
            const matchingProject = projects.find((project) => project.key === flags.project)
            if(!matchingProject) {
                throw(`There is no project with the key ${flags.project} in this organization`)
            }
            return matchingProject
        }
        return null
    }

    private async selectOrganization(organization: Organization) {
        const ssoAuth = new SSOAuth()
        this.token = await ssoAuth.getAccessToken(organization)
        storeAccessToken(this.token, this.authPath)
    }
}