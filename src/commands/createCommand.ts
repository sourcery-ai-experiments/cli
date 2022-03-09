import { Flags } from '@oclif/core'
import { ClassConstructor, plainToClass } from 'class-transformer'
import { validateSync } from 'class-validator'
import inquirer from 'inquirer'
import { reportValidationErrors } from '../utils/reportValidationErrors'
import Base from './base'

export default abstract class CreateCommand<ResourceType> extends Base {
    prompts:inquirer.QuestionCollection = []
    authRequired = true
    static flags = {
        ...Base.flags,
        'field': Flags.string({
            description: 'Specify a changed field in the format <key>,<value>'
        })
    }

    public async populateParameters(paramClass:ClassConstructor<ResourceType>): Promise<ResourceType> {
        const { flags } = await this.parse(CreateCommand)
        console.log({flags})
        await this.requireProject()
        const answers = await this.populateParametersWithInquirer()
        const params = plainToClass(paramClass, answers)
        const errors = validateSync(params as Record<string, unknown>, {
            whitelist: true
        })
        reportValidationErrors(paramClass.name, errors)
        return params
    }

    private async populateParametersWithInquirer() {
        return await inquirer.prompt(this.prompts, {
            token: this.token,
            projectKey: this.projectKey
        })
    }
}