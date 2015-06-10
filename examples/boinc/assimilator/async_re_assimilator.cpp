// This file is part of BOINC.
// http://boinc.berkeley.edu
// Copyright (C) 2008 University of California
//
// BOINC is free software; you can redistribute it and/or modify it
// under the terms of the GNU Lesser General Public License
// as published by the Free Software Foundation,
// either version 3 of the License, or (at your option) any later version.
//
// BOINC is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
// See the GNU Lesser General Public License for more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with BOINC.  If not, see <http://www.gnu.org/licenses/>.

// An assimilator for the Asynchronous RE software that:
// 1) if success, copy the output file(s) to a directory:
//      <rootdir>/<jobname>/r<replica>/<jobname>_<cycle>.out etc.
//        where  jobname replica cycle are encoded in the 
//        work unit name such as ttr_r10_c2_0
// 2) if failure, append a message to an error log

#include <vector>
#include <string>
#include <cstdlib>

#include "boinc_db.h"
#include "error_numbers.h"
#include "filesys.h"
#include "sched_msgs.h"
#include "validate_util.h"
#include "sched_config.h"

using std::vector;
using std::string;

#include <stdlib.h>
#include <string.h>
#include <regex.h>


int write_error(char* p) {
    static FILE* f = 0;
    if (!f) {
        f = fopen(config.project_path("async_re/errors"), "a");
        if (!f) return ERR_FOPEN;
    }
    fprintf(f, "%s", p);
    fflush(f);
    return 0;
}

// parses the work unit name and returns the destination directory
// for the output files and the relevant info
char *asyncre_repldir(const char *wuname, char **jobname, int *replica, int *cycle){
  static char path[MAXPATHLEN];
  static char job[MAXPATHLEN];

  regex_t reg;          // compiled regex
  int nmatch = 4;       // at most 4 substring matches (0 is the entire string?) 
  regmatch_t pmatch[4]; // matched string pointers

  char match[MAXPATHLEN];
  const char *dest_dir;
  size_t size;
  char bufh[1024];

  // error outputs
  strncpy(path,config.project_path("async_re"),MAXPATHLEN-1);
  *jobname = NULL;
  *replica = -1;
  *cycle = -1;

  if(regcomp(&reg, "^(.+)_r([0-9]+)_c([0-9]+)", REG_EXTENDED) != 0){
    // regex compilation has failed. Should never happen? 
    sprintf(bufh, "%s\n", "asyncre_repldir(): error in regcomp");
    write_error(bufh);
    return path;
  }

  if(regexec(&reg, wuname, nmatch, pmatch, 0) != 0){
    // wu name does not match pattern;
    sprintf(bufh, "%s\n", "asyncre_repldir(): warning wu name does not fit pattern");
    write_error(bufh);
    return path;
  }
  
  //retrieve jobname
  size = pmatch[1].rm_eo - pmatch[1].rm_so;
  strncpy(job, &wuname[pmatch[1].rm_so], size);
  job[size] = '\0';
  
  //replica number
  size = pmatch[2].rm_eo - pmatch[2].rm_so;
  strncpy(match, &wuname[pmatch[2].rm_so], size);
  match[size] = '\0';
  *replica = atoi(match);

  //cycle number
  size = pmatch[3].rm_eo - pmatch[3].rm_so;
  strncpy(match, &wuname[pmatch[3].rm_so], size);
  match[size] = '\0';
  *cycle = atoi(match);

  //prepares directory
  boinc_mkdir(config.project_path("%s/%s", "async_re", job));
  dest_dir = config.project_path("%s/%s/r%d", "async_re", job, *replica);
  boinc_mkdir(dest_dir);
  strncpy(path,dest_dir,MAXPATHLEN-1);

  regfree(&reg);
  *jobname = job;
  return path;
}



int assimilate_handler(
    WORKUNIT& wu, vector<RESULT>& /*results*/, RESULT& canonical_result
) {
    int retval;
    char buf[1024];
    unsigned int i;
    char *repldir;
    char *jobname = NULL;
    int replica, cycle;
    bool asyncre_mode = true;

    // retval = boinc_mkdir(config.project_path("async_re"));
    // if (retval) return retval;

    //retrieve replica directory from wu name
    asyncre_mode = true;
    repldir = asyncre_repldir(wu.name, &jobname, &replica, &cycle);
    if(!repldir || !jobname){
      //wu name does not fit expected pattern
      //repldir has been given the default value (sampl_results) in project directory
      asyncre_mode = false;
    }

    if (wu.canonical_resultid) {
        vector<OUTPUT_FILE_INFO> output_files;
        const char *copy_path;
        get_output_file_infos(canonical_result, output_files);
        unsigned int n = output_files.size();
        bool file_copied = false;	

        for (i=0; i<n; i++) {
            OUTPUT_FILE_INFO& fi = output_files[i];

	    if(asyncre_mode){

	      if (n == 3){ // regular output

		if(i==0){
		  //out file
		  copy_path = config.project_path("async_re/%s/r%d/%s_%d.out", jobname, replica, jobname, cycle);
		}else if(i==1){
		  //dms file
		  copy_path = config.project_path("async_re/%s/r%d/%s_%d.dms", jobname, replica, jobname, cycle);
		}else if(i==2){
		  //rst file
		  copy_path = config.project_path("async_re/%s/r%d/%s_%d.rst", jobname, replica, jobname, cycle);	
		}else{
		  //?
		  copy_path = config.project_path("async_re/%s/r%d/%s_%d_%d",  jobname, replica, jobname, cycle, i);
		}

	      }else if(n == 4){ // BEDAM output


		if(i==0){
		  //out file
		  copy_path = config.project_path("async_re/%s/r%d/%s_%d.out", jobname, replica, jobname, cycle);
		}else if(i==1){
		  //dms file 1 (receptor)
		  copy_path = config.project_path("async_re/%s/r%d/%s_rcpt_%d.dms", jobname, replica, jobname, cycle);
		}else if(i==2){
		  //dms file 2 (ligand)
		  copy_path = config.project_path("async_re/%s/r%d/%s_lig_%d.dms", jobname, replica, jobname, cycle);
		}else if(i==3){
		  //rst file
		  copy_path = config.project_path("async_re/%s/r%d/%s_%d.rst", jobname, replica, jobname, cycle);	
		}else{
		  //?
		  copy_path = config.project_path("async_re/%s/r%d/%s_%d_%d",  jobname, replica, jobname, cycle, i);
		}

	      }else{

		// unexpected number of async_re output files
		if (n==1) {
		  copy_path = config.project_path("async_re/%s", wu.name);
		} else {
		  copy_path = config.project_path("async_re/%s_%d", wu.name, i);
		}
		
	      }

	    }else{

	      // non-async_re output 
	      if (n==1) {
                copy_path = config.project_path("async_re/%s", wu.name);
	      } else {
                copy_path = config.project_path("async_re/%s_%d", wu.name, i);
	      }

	    }

	    retval = boinc_copy(fi.path.c_str() , copy_path);
	    if (!retval) {
	      file_copied = true;
	    }

        }
        if (!file_copied) {
            copy_path = config.project_path(
                "async_re/%s_%s", wu.name, "no_output_files"
            );
            FILE* f = fopen(copy_path, "w");
            fclose(f);

	    // flag error
	    if(asyncre_mode){
	      copy_path = config.project_path("async_re/%s/r%d/%s_%d.failed", jobname, replica, jobname, cycle);
	      f = fopen(copy_path, "w");
	      fclose(f);
	      sprintf(buf, "warning: cycle %d of replica %d of job %s (work unit = %s) failed with error: 0x%x\n", cycle, replica, jobname, wu.name, wu.error_mask);
	    }

	    sprintf(buf, "warning: work unit = %s failed with error: 0x%x\n", wu.name, wu.error_mask);
	    return write_error(buf);

        }
    } else {
      if(asyncre_mode){
	// create an empty .failed file so it will be detected as a failure
        const char *copy_path;
	copy_path = config.project_path("async_re/%s/r%d/%s_%d.failed", jobname, replica, jobname, cycle);
	FILE *f = fopen(copy_path, "w");
	fclose(f);
	sprintf(buf, "warning: cycle %d of replica %d of job %s (work unit = %s) failed with error: 0x%x\n", cycle, replica, jobname, wu.name, wu.error_mask);
      }
      sprintf(buf, "warning: work unit = %s failed with error: 0x%x\n", wu.name, wu.error_mask);
      return write_error(buf);
    }

    
    return 0;
}
