#!/usr/bin/perl -w

# a perl script to calculate the number of exchanges per cycle for each replica 
#
# Junchao Xia, Apr. 01, 2015
my $rbgn = $ARGV[0];
my $rend = $ARGV[1];

@nEX_tt = ();
@ncycle = (); 

open(OUTPUT, ">numEXdata.dat");

for (my $ir = $rbgn; $ir <= $rend;  $ir++)
{
   system "wc -l r$ir/state.history > r$ir/nattemptEX.dat";
   system "tail -n 1 r$ir/state.history | awk \'{print \$1}\' > r$ir/ncycle.dat"; 
   open(INPUT, "r$ir/nattemptEX.dat");
   while(<INPUT>) #read in data
   {
       chomp;
       my @tmp_array=split;
       if (defined $tmp_array[0] )
       {
          push (@nEX_tt,$tmp_array[0]) ;
       }
   }
   close(INPUT);
   open(INPUT, "r$ir/ncycle.dat");

   while(<INPUT>) #read in data
   {
       chomp;
       my @tmp_array=split;
       if (defined $tmp_array[0] )
       {
          push (@ncycle,$tmp_array[0]) ;
       }
   }
   close(INPUT);
   printf OUTPUT "%20d %20d %20d %20f \n", $ir, $nEX_tt[$ir], $ncycle[$ir], $nEX_tt[$ir]/$ncycle[$ir];

}

my $sum_ntt = 0.0;
my $sum_npc = 0.0;
my $sum_ncy  = 0.0;

for ($ip = 0; $ip <=$#ncycle; $ip ++)
{
  $sum_ntt += $nEX_tt[$ip];
  $sum_npc += $nEX_tt[$ip]/$ncycle[$ip]; 
  $sum_ncy += $ncycle[$ip];
}

$sum_ntt /= ($#nEX_tt+1);
$sum_npc /= ($#nEX_tt+1);
$sum_ncy /= ($#nEX_tt+1);
printf "%20f %20f %20f \n", $sum_ntt, $sum_npc, $sum_ncy;
close(OUTPUT)



	  
