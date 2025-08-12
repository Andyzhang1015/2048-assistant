class Test {
  constructor(name, age) {
    this.name = name;
    this.age = age;
  }

  sayHello() {
    return `Hello, ${this.name} ${this.age} years old.`;
  }
}

const test = new Test("John", 30);
console.log(test.sayHello()); // "Hello, John 30 years old."