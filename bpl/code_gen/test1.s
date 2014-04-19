	.section .rodata
	.WriteIntString: .string "%d "
	.WritelnString: .string "\n"
	.WriteStringString: .string "%s "
	.ArrayOverflowString: .string "You fell off the end of an array.\n"
	.ReadIntString: .string "%d"
	.HiBobString: .string "Hi, Bob!"
	.text
	.globl main
main:
	movq $.HiBobString, %rsi
	movq $.WriteStringString, %rdi
	movq $0, %rax
	call printf

	movq $.WritelnString, %rdi
	movq $0, %rax
	call printf
