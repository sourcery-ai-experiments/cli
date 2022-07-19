import chalk from "chalk"
import { togglebot, togglebotSleep, togglebotWink } from "./togglebot"

export default class Writer {
    public successMessage(message:string):void {
        if(!this.headless) console.log(chalk.green(`✅ ${message}`))
    }
    
    public failureMessage(message:string):void {
        if(!this.headless) console.log(chalk.red(`❌ ${message}`))
    }
    
    public statusMessage(message:string):void {
        if(!this.headless) console.log(chalk.yellow(`🤖 ${message}`))
    }

    public blankLine():void {
        if(!this.headless) console.log('\n\r')
    }

    public showResults(results:unknown):void {
        console.log(JSON.stringify(results, null, 2))
    }

    public showTogglebot() {
        if(!this.headless) console.log(togglebot)
    }

    public showTogglebotWink() {
        if(!this.headless) console.log(togglebotWink)
    }

    public showTogglebotSleep() {
        if(!this.headless) console.log(togglebotSleep)
    }

    public headless:boolean
}