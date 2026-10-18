
/* S2 cpu micro architecture simulator

	modify from s1 Computer Architecture 		1997, 1998


	s2   										5 Dec 2001
   	s21  										18 Jan 2007


	simplify (direct) for calculator project	29 Jan 2016
   	no Z, S
   	add address trace (Chinese new year)		10 Feb 2016
 	add interrupt 								27 Mar 2016
	add MOS										1 Apr 2016
	most MOS is in assembly	(Happy Songkran)
	and fix "trap 16" bug					  	13 Apr 2016

	redo for teaching interrupt programming		8 Nov 2016
	add io										19 Nov 2016
	update to "grandfather s21"	(Chinese NY)	28 Jan 2017
 	add: readinputstring 						1 Feb 2017
	update clean up code						28 Jan 2025

   Prabhas Chongstitvatana
   Department of Computer Engineering
   Chulalongkorn University

*/

#include "s21.h"

extern int timer0range, timer1range;
extern int display;

int R[32], Ir, Pc, M[MAXMEM]; // RetAds;
int intflag, intmask[4], intrq[4], intnum;
int runflag, savePc, cpuflag;
int heapfree = HEAP;
int clock, ninst;

int signx2( int d ){	// sign bit 21 extended
	if( d & 0x0200000 ) return d | 0xFFC00000;
	return d;
}

PRIVATE char buf[80];		// input buffer

PRIVATE int myalloc(int k){
	int a;
	a = heapfree;
	heapfree += k;
	if( heapfree > MAXMEM )
		error("malloc: out of memory");
//	printf("malloc %d heapfree %d\n",k,heapfree);
	return a;
}

PRIVATE void trap( int reg, int num ){	// special function
	int n, i;

	switch( num ) {
	case 0:  // stop
		runflag = 0;
//		printf("stop, clock %d, execute %d instructions\n",clock,ninst);
		break;
	case 1: printf("%d ",R[reg]);  break;  // print integer
	case 2: printf("%c",R[reg]);  break;   // printc char
	case 3: 					// printstring
		i = R[reg];				// pointer to string
		while( M[i] != 0 ){
			printf("%c", M[i]);
			i++;
		}
		break;
	case 4: // input (return string)
		scanf("%s",buf);
		i = 0;
		while( buf[i] != 0 ){		// copy to M[]
			M[STRSEG+i] = buf[i];
			i++;
		}
		M[STRSEG+i] = 0;		// terminate string
//		printf("%s\n",buf);
		R[RETV] = STRSEG;		// return pointer to string
		break;

	case 13: timer0range = R[reg]; break; // set timer0
	case 14: timer1range = R[reg]; break; // set timer1

	case 18:
		n = R[reg];				// port number
		R[RETV] = readport(n);
		break;
	case 19: R[RETV] = myalloc(R[reg]); break;	// malloc

	}
}

void interrupt(int n){
	if( n > 3 )
		error("unknown interrupt");
	printf("interrupt%d\n",n);
	intnum = n;
	R[31] = Pc;			// save pc
	Pc = M[INTVEC+n];
	cpuflag = 1; 		// wake up sleepy cpu
	intflag = 0;		// master disable interrupt
	intrq[n] = 0;		// clear int request
}

void run(void){		// execute one instruction
	int ads, d, r1, r2, r3, i;

	savePc = Pc;
	Ir = M[Pc];		// instruction fetch
	Pc++;
	ads = IRads();	// decode
	d = IRdisp();	// signx  17-bit
	r1 = IRr1();
	r2 = IRr2();
	r3 = IRr3();
	ninst++;
	switch( IRop() ) {
	case NOP:  break;
	case LDA:  R[r1] = M[ads]; break;
	case LDD:  R[r1] = M[R[r2]+d];  break;
	case STA:  M[ads] = R[r1];  break;
	case STD:  M[R[r2]+d] = R[r1];  break;
	case MVI:  R[r1] = signx2(ads); break;
	case JMP:  Pc = ads; break;
	case JAL:  R[r1] = Pc; Pc = ads; break;
	case JT: if( R[r1] != 0 ) Pc = ads; break;
	case JF: if( R[r1] == 0 ) Pc = ads; break;
	case ADDI: R[r1] = R[r2] + d; break;
	case SUBI: R[r1] = R[r2] - d; break;
	case MULI: R[r1] = R[r2] * d; break;
	case DIVI: R[r1] = R[r2] / d; break;
	case ANDI: R[r1] = R[r2] & d; break;
	case ORI:  R[r1] = R[r2] | d; break;
	case XORI: R[r1] = R[r2] ^ d; break;
	case EQI:  R[r1] = R[r2] == d; break;
	case NEI:  R[r1] = R[r2] != d; break;
	case LTI:  R[r1] = R[r2] <  d; break;
	case LEI:  R[r1] = R[r2] <= d; break;
	case GTI:  R[r1] = R[r2] >  d; break;
	case GEI:  R[r1] = R[r2] >= d; break;
	case SHLI: R[r1] = R[r2] << d; break;
	case SHRI: R[r1] = R[r2] >> d; break;
	case MODI: R[r1] = R[r2] %  d; break;
	case XOP:
		switch( IRxop() ){
		case ADD:  R[r1] = R[r2] + R[r3]; break;
		case SUB:  R[r1] = R[r2] - R[r3]; break;
		case MUL:  R[r1] = R[r2] * R[r3]; break;
		case DIV:  R[r1] = R[r2] / R[r3]; break;
		case AND:  R[r1] = R[r2] & R[r3]; break;
		case OR:   R[r1] = R[r2] | R[r3]; break;
		case XOR:  R[r1] = R[r2] ^ R[r3]; break;
		case EQ:   R[r1] = R[r2] == R[r3]; break;
		case NE:   R[r1] = R[r2] != R[r3]; break;
		case LT:   R[r1] = R[r2] <  R[r3]; break;
		case LE:   R[r1] = R[r2] <= R[r3]; break;
		case GT:   R[r1] = R[r2] >  R[r3]; break;
		case GE:   R[r1] = R[r2] >= R[r3]; break;
		case SHL:  R[r1] = R[r2] << R[r3]; break;
		case SHR:  R[r1] = R[r2] >> R[r3]; break;
		case MOD:  R[r1] = R[r2] %  R[r3]; break;
		case MOV:  R[r1] = R[r2]; break;
		case LDX:  R[r1] = M[R[r2] + R[r3]]; break;
		case STX:  M[R[r2] + R[r3]] = R[r1]; break;
		case RET:  Pc = R[r1]; break;
		case TRAP: trap(r1,r2); break;
		case PUSH:
			R[r1]++;			// increment stack pointer
			M[R[r1]] = R[r2];
			break;
		case POP:
			R[r2] = M[R[r1]];
			R[r1]--;			// decrement stack pointer
			break;
		case NOT:  R[r1] = (R[r2] == 0) ? ~0 : 0;  break;

		case INT:  interrupt(r2); break;
		case RETI:
			Pc = R[31];
			intflag = 1;	// enable interrupt
			break;
//		case EI:  intmask[r2] = 1; break;
//		case DI:  intmask[r2] = 0; break;
		case WFI: cpuflag = 0; break; // put cpu to sleep
		default:
//			printf("xop %d\n",IRxop());
			error("undefine xop");
		}
		break;
	default:
		error("undefine op");
	}
}

void checkinterrupt(void){
	if( intflag ){
		if( intmask[0] && intrq[0] ) interrupt(0);
		else if( intmask[1] && intrq[1] ) interrupt(1);
		else if( intmask[2] && intrq[2] ) interrupt(2);
		else if( intmask[3] && intrq[3] ) interrupt(3);
	}
}

//  run one instruction and check interrupt
void runoneclock(void){
	clock++;
	simdevices();
	if( runflag && cpuflag ){
		run();
		if( display ) show();
	}
//	if( (Ir & 0xF83E0FFF) == 0xF8200014 )	// trap 16, ei
//		 ;     // do not interrupt just after ei
//	else
		checkinterrupt();
}


int main(int argc, char *argv[]){
	if( argc < 2 ) {
		printf("usage : sim21 objfile\n");
		printf("usage : sim21 -d objfile, disassemble\n");
		exit(0);
	}

//	bindsym();

	display = 1;
	init_io();
	clock = 0;
	ninst = 0;
	Pc = 0;
	runflag = 1;
	cpuflag = 1;
	intflag = 1;	// master enable interrupt
	intmask[0] = 1;
	intmask[1] = 0;
	intmask[2] = 0;
	intmask[3] = 0;

	if( *argv[1] == '-' && *(argv[1]+1) == 'd' ){
		loadprogram(argv[2]);
		printf("%s\n",argv[2]);
		disAll();
		exit(0);
	}

	loadprogram(argv[1]);
//	bindsym();
	interp();
	printf("stop, clock %d, execute %d instructions\n",clock,ninst);

	return 0;
}

