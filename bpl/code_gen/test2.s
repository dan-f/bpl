	.section .rodata
	.WriteIntString: .string "%d "
	.WritelnString: .string "\n"
	.WriteStringString: .string "%s "
	.ArrayOverflowString: .string "You fell off the end of an array.\n"
	.ReadIntString: .string "%d"
	.text
	.globl main
f:
	## f is the factorial function, with one argument
	## set up FP by moving SP into FP
	movq %rsp, %rbp
	## decrement the stack pointer by enough to allocate local variables (none in this case)
	subq $0, %rsp
	## body of f
	## place our arg in the accumulator, and compare it to 0
	movq 16(%rbp), %rax
	# cmpl $0, %eax
	cmpq $0, %rax
	jg L2
	## n equals 0, so return 1
	movq $1, %rax		#put 1 in accumulator
	movq %rbp, %rsp		#move frame pointer into stack pointer
	ret			#return
L2:
	## n does not equal 0, so recurse
	## push n onto stack for n * (...)
	movq 16(%rbp), %rax
	push %rax
	## function call
	movq 16(%rbp), %rax
	push %rax		#push n onto stack for n - 1
	movq $1, %rax
	subq %rax, 0(%rsp)	#subtracts 1 from n, which is top-of-stack
	movq 0(%rsp), %rax
	addq $8, %rsp		#pop n-1 back off of stack
	push %rax		#push n-1 onto stack
	push %rbp
	call f
	## on return
	pop %rbp		#restore fp
	addq $8, %rsp		#pop arg
	## n is now on top of stack, f(n-1) in %rax
	imul 0(%rsp), %eax	#unsure about this
	movq %rbp, %rsp		#move fp into sp
	ret			#return
main:
	movq %rsp, %rbp
	subq $0, %rsp
	push $5			#n == 5
	push %rbp
	call f
	pop %rbp		#restore fp
	addq $8, %rsp		#pop arg off stack
	movq %rax, %rsi
	movq $.WriteIntString, %rdi
	movq $0, %rax
	call printf
	## print newline
	movq $.WritelnString, %rdi
	movq $0, %rax
	call printf
