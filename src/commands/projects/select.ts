import AuthCommand from '../authCommand'
export default class SelectProject extends AuthCommand {
    static description = 'Select which organization to access through the API'
    static hidden = false
    authRequired = true

    public async run(): Promise<void> {
        await this.setProject()
    }
}