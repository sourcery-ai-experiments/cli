import { JavascriptEngine } from './JavascriptEngine'

const [filename, variableString, optionsString] = process.argv
const variable = JSON.parse(variableString)
const options = JSON.parse(optionsString)
const engine = new JavascriptEngine(filename, variable, options)
engine.refactor()