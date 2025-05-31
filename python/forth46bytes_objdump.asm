
../forth46bytes.bin:     file format binary


Disassembly of section .data:

00000000 <.data>:
   0:	50                   	push   %ax
   1:	b8 8e 00             	mov    $0x8e,%ax
   4:	31 d8                	xor    %bx,%ax
   6:	e8 ff 00             	call   0x108
   9:	17                   	pop    %ss
   a:	00 3c                	add    %bh,(%si)
   c:	05 75 00             	add    $0x75,%ax
   f:	ea 50 00 3c 00       	ljmp   $0x3c,$0x50
  14:	74 01                	je     0x17
  16:	eb 02                	jmp    0x1a
  18:	e8 ee 00             	call   0x109
  1b:	05 05 88             	add    $0x8805,%ax
  1e:	eb 47                	jmp    0x67
  20:	b8 e6 02             	mov    $0x2e6,%ax
  23:	00 d2                	add    %dl,%dl
  25:	31 14                	xor    %dx,(%si)
  27:	cd e4                	int    $0xe4
  29:	80 75 80 c3          	xorb   $0xc3,-0x80(%di)
  2d:	f4                   	hlt
