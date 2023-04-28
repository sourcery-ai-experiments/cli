import { Flags } from '@oclif/core'
import inquirer from 'inquirer'

import {
    fetchEnvironmentByKey,
    generateSdkKeys,
    invalidateSdkKey,
    Environment,
    GenerateSdkTokensDto,
} from '../../api/environments'
import { environmentChoices, environmentPrompt, sdkKeyTypePrompt } from '../../ui/prompts'
import Base from '../base'

export default class RotateKeys extends Base {
    static hidden = false
    static description = 'Rotate SDK keys for an environment'
    static flags = {
        ...Base.flags,
        env: Flags.string({
            description: 'Environment to rotate keys for',
            required: false,
        }),
        type: Flags.enum({
            options: ['client', 'mobile', 'server'],
            description: 'The type of SDK key to rotate',
        }),
    }
    authRequired = true

    public async run(): Promise<void> {
        const { flags } = await this.parse(RotateKeys)
        await this.requireProject()
        const token = this.token

        if (flags.headless && !flags.env) {
            throw new Error('In headless mode, the env flag is required')
        }

        const environmentKey = await this.getEnvironmentKey()

        const environment = await fetchEnvironmentByKey(
            token,
            this.projectKey,
            environmentKey,
        )
        console.log(environment)

        if (!environment) {
            console.log('nopw')

            return
        }

        const sdkType = await this.getSdkType()
        console.log('fffff')

        if (sdkType) {
            // Generate new SDK key
            const requestBody: GenerateSdkTokensDto = {
                types: [sdkType],
            }
            const updatedEnvironment: Environment = await generateSdkKeys(
                token,
                this.projectKey,
                environmentKey,
                requestBody,
            )
            console.log('aaaaaaa')

            // Invalidate the old SDK key
            const activeKeys = environment.sdkKeys[sdkType]
            const oldKey = activeKeys[activeKeys.length - 1].key

            try {
                console.log('AAAAAA')
                await invalidateSdkKey(token, this.projectKey, environmentKey, oldKey)
        
                // Log success message
                this.log(`Successfully rotated ${sdkType} SDK key for environment ${environmentKey}`)
                this.log(`New ${sdkType} SDK key: ${updatedEnvironment.sdkKeys[sdkType][0].key}`)
            } catch (error) {
                // Log failure message
                this.error(`Failed to rotate ${sdkType} SDK key for environment ${environmentKey}`)
            }

        }
    }

    private async getEnvironmentKey(): Promise<string> {
        const { flags } = await this.parse(RotateKeys)

        if (flags.env) {
            return flags.env
        }

        // Create a modified environmentPrompt object with the updated choices property
        const environmentPromptWithToken = {
            ...environmentPrompt,
            // Pass the token and projectKey to the environmentChoices function
            choices: await environmentChoices(this.token, this.projectKey),
        }

        // Pass the modified environmentPrompt object to inquirer.prompt
        const { environment } = await inquirer.prompt([environmentPromptWithToken])
        return environment.key
    }
    
    private async getSdkType(): Promise<string | undefined> {
        const { flags } = await this.parse(RotateKeys)
    
        if (flags.type) {
            return flags.type
        }
    
        const { sdkType } = await inquirer.prompt([sdkKeyTypePrompt])
        return sdkType
    }
}
