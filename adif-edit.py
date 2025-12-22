# Initial incept  12/2/2025
# V1.05 12/21/2025
# copyright 2025, Christian Claborne, The Ham Ninja, N1CLC
# licensed under the GNU General Public License (GPL), specifically version 2 (GPLv2)
# I needed an app to modify ADIF files so I used claude.ai for a draft 
# then modified to fit my needs as well as fixing a bug created by claude.ai
# My initial needs could be met in just a few lines of code but this is more flexible

# USAGE: edit-adif -h
# If no arguments are passed, it outputs help on usage and prompts you for all values

# Mainly used to add data for the ADIF <other> field for importing to AC Log

# See release-notes for version history
############################

import re
import sys
import time

def help():
    print(f"""
Version: 1.05

Usage:
   {sys.argv[0]} [-h | <input_file>] [<output_file | -f>] [<value> | -f] [<field_name> | -f]
   
NOTE: Defaults are hard coded in the script at the top of the entry point):

{sys.argv[0]} -h for help.

- input_file 
    The adif formatted file you want to process
    (if argument is blank, all arguments should be left blank causing the app 
    to prompt the user for the input_file and other required arguments.)


- output_file 
    File where you want the processed data to be placed
    (If the argument is blank all following arguments should be left blank, causing the app to prompt the user 
    for the output file name and the rest of the arguments.)

    “-f” will force override mode, forcing default values for this and all subsequent parameters (defined above), 
    skipping the confirmation step.
    
    “-c” puts the app into override mode like -f and runs a second replace on the default output file by adding
    or changing MY_GRIDSQUARE to the default set.  This was needed for pure chase logs from PoLo since it doesn't
    supply MY_GRIDSQUARE when only chasing.

- value 
    The value that you want to be put in the field
    (If the argument left blank, all following arguments should be left blank, causing the app to prompt the user 
    for the value and field_name)
    If -f is used, it forces defaults for this and the field_name (defined above).

    NOTE: If you want the field created with no value, execute the script with only the input file name, and supply a 
    blank when prompted for the activity.

- field_name or “-f”
    The name of the field that should be either edited (changed to the new value) or it’s added if it’s not there.  
    If the user enters “-f” as the final argument, it will force the app to use the default field (defined above).
    (If the argument is not passed, the user will be prompted for the value). 
    
    """)



def parse_adif_record(record):
    """
    Parse an ADIF record and extract field-value pairs.
    Returns a dictionary of fields and the raw record.
    """
    fields = {}
    # Pattern to match ADIF fields: <FIELD:length>value or <FIELD:length:type>value
    pattern = r'<(\w+):(\d+)(?::(\w))?>([^<]*)'

    for match in re.finditer(pattern, record):
        field_name = match.group(1).upper()
        length = int(match.group(2))
        value = match.group(4)[:length]
        fields[field_name] = value

    return fields


def add_field_to_record(record, field_name, field_value):
    """
    Add or update a field in an ADIF record before the <EOR> marker.
    If the field already exists, it will be replaced with the new value.
    """
    # Create the new field in ADIF format
    new_field = f"<{field_name}:{len(field_value)}>{field_value}"

    # Check if the field already exists
    # Pattern to match the specific field: <FIELDNAME:length>value or <FIELDNAME:length:type>value
    field_pattern = rf'<{field_name}:\d+(?::\w)?>[^<]*'

    if re.search(field_pattern, record, re.IGNORECASE):
        # Field exists, replace it
        updated_record = re.sub(field_pattern, new_field, record, flags=re.IGNORECASE)

        # quigmod put the EOR back
        # This is a hack because I don't know why the EOR is getting stripped off!!!!!!!!!
        updated_record = updated_record + " <EOR>"
    else:
        # Field doesn't exist, add it before <EOR>
        if '<EOR>' in record.upper():
            # Insert before <EOR>
            eor_pos = record.upper().rfind('<EOR>')
            updated_record = record[:eor_pos] + new_field + ' ' + record[eor_pos:]
        else:
            # If no <EOR>, just append the field
            updated_record = record.strip() + ' ' + new_field + ' <EOR>\n'

    return updated_record


def update_adif_file(input_file, output_file, field_name, field_value):
    """
    Read an ADIF file, add a field to each record, and write to output file.
    """
    try:
        #with open(input_file, 'r', encoding='utf-8') as f:  #fixes a bug where a dump file contains something it doesn't like.
        with open(input_file, 'r') as f:
            content = f.read()

        # Split content into header and records
        # ADIF header ends with <EOH>
        if '<EOH>' in content.upper():
            header_end = content.upper().find('<EOH>') + 5
            header = content[:header_end]
            records_section = content[header_end:]
        else:
            header = ""
            records_section = content

        # Split records by <EOR>
        records = re.split(r'<EOR>', records_section, flags=re.IGNORECASE)

        updated_records = []
        record_count = 0
        updated_count = 0
        added_count = 0

        for record in records:
            record = record.strip()
            if record:  # Skip empty records
                # Check if field already exists
                field_pattern = rf'<{field_name}:\d+(?::\w)?>[^<]*'
                field_exists = bool(re.search(field_pattern, record, re.IGNORECASE))

                updated_record = add_field_to_record(record, field_name, field_value)
                updated_records.append(updated_record)
                record_count += 1

                if field_exists:
                    updated_count += 1
                else:
                    added_count += 1

        # Write to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            if header:
                f.write(header + '\n')
            f.write('\n'.join(updated_records))

        print(f"✅ Successfully processed {record_count} records")
        print(f"  - Added {field_name} to {added_count} records")
        print(f"  - Updated {field_name} in {updated_count} records")
        print(f"✅ Output written to: {output_file}")
        return True

    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        return False
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

#############################################################
#####                     Entry Point                   #####
#############################################################
def main():
    #########################################################
    ##########         D E B U G                   ##########
    #########################################################
    #print(f"arg 0 is {sys.argv[0]}, arg 1 is {sys.argv[1]}, arg 2 is {sys.argv[2]}")
    #
    #print("\nQuitting.")
    #sys.exit()  # user wants to exit
    ##########################################################

    # Setup any defaults needed
    default_output_file_name = 'C:\\Users\\micro\\Documents\\Affirmatech\\N3FJP Software\\ACLog\\foo.adi'
    default_field_value = 'SOTA'
    default_field_name = 'OTHER'
    default_chase_file_name = 'C:\\Users\\micro\\Documents\\Affirmatech\\N3FJP Software\\ACLog\\bar.adi'
    default_MY_GRIDSQUARE = 'DM12kw'

    user_override = 'N'
    chase_mode = 'N'

    # setup a timer
    start_time = time.perf_counter()

    print(f"\n=== ADIF Field Updater ===")

    """Main function to run the ADIF updater."""
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = ""

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = ""


    if len(sys.argv) > 3:
        field_value = sys.argv[3].upper()
    else:
        field_value = ""

    if len(sys.argv) > 4:
        field_name = sys.argv[4].upper()
    else:
        field_name = ""  # initialize the field

    if output_file.upper() == '-F':
        user_override = 'Y'
        output_file = default_output_file_name
        field_value = default_field_value
        field_name = default_field_name

    if output_file.upper() == '-C':
        user_override = 'Y'
        chase_mode = 'Y'
        output_file = default_output_file_name  # This is for the first pass
        field_value = "CHASE"  # This is for the first run (it changes later for the second run)
        field_name = default_field_name # This is for the first run (it changes later for the second run)

    # If user want's some help
    if input_file == "-h":
        help()
        sys.exit()  # exit because we are just giving help

    # Get input file
    if input_file == output_file:  #input can't equal output
        input_file = ""
        print(f"\nERROR!: INPUT FILE CAN NOT EQUAL OUTPUT FILE NAME\n")

    if not input_file:
        print(f"\nUSAGE: {sys.argv[0]} <input_file> <output_file> <activity> <output file>")
        print(f"   or use {sys.argv[0]} -h for help")
        input_file = input("\nEnter INPUT ADIF file path or Q to QUIT: ").strip()

        if input_file.strip().upper() == "Q":
            print("\nQuitting.")
            sys.exit()  # user wants to exit

    # Get output file or use the default

    if not output_file:
        default_output = input_file.replace('.adi', '_updated.adi').replace('.adif', '_updated.adif')
        if not default_output.endswith(('.adi', '.adif')):
            default_output += '_updated.adi'

        output_file = input(f"Enter OUTPUT file path (default: {default_output}): ").strip()
        if not output_file:
            output_file = default_output


##########################################################
############## FIELD VALUE PROCESSING         ############
##########################################################

    passed = 0
    while passed == 0:
        # user may not supply activity on the command line so prompt for it
        # We will prompt for a value but the user can override causing null to be placed in the field (strange but true)
        if not field_value:
            # Prompt the user for replacement text
            field_value = input(
                "\nEnter text for other field (ex SOTA|POTA|CHASE|HUNT|FIELD|CONTEST) [q to quit]: ").strip().upper()

        if field_value.strip().upper() == "Q":
            print("\nQuitting.")
            sys.exit()  # user wants to exit

        if field_value == "-F":
            field_value = default_field_value
            field_name = default_field_name
            user_override = 'Y'

        # Check user input
        if field_value not in ["SOTA", "POTA", "SPOTA", "CHASE", "HUNT", "FIELD", "CONTEST", "DM12KW"]:
            # print("\nYou must enter one of the following: SOTA, POTA, SPOTA, CHASE, HUNT, FIELD, CONTEST.")
            print("\nI expected one of the following: SOTA, POTA, SPOTA, CHASE, HUNT, FIELD, CONTEST.")

            user_override = "N"
            user_override = input("Do you want to OVERRIDE?: (y/n): ").strip().upper()
            if user_override.strip().upper() == "Q":
                print("\nQuitting.")
                sys.exit()  # user wants to exit
                
            if user_override.strip().upper() == "Y":
                passed = 1
            else:
                passed = 0
                field_value = ""  # null the value in case junk was set
        else:
            # everything looks good
            passed = 1

    ##########################################################

    if field_name.upper() != '-F':   # we don't want to force it
        #print(f"The field name is currently set to {field_name}")
        # Get field name to add or update  (default to "OTHER")
        if not field_name:  # nothing was passed on the command line
            field_name = input("Enter field name to add or update (default: " + default_field_name +", q to Quit): ").strip().upper()
            
            if field_name == "Q":
                print("\nQuitting.")
                sys.exit()  # user wants to exit

            if not field_name:  # user entered nothing
                field_name = default_field_name
    else:
        field_name = "OTHER"
        user_override = "Y"

    # Confirm before proceeding
    print(f"\nWill add/update <{field_name}:{len(field_value)}>{field_value} to all records")
    print(f"(Existing {field_name} fields will be updated with the new value)")
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")

    if user_override == 'N':
        confirm = input("\nProceed? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled")
            return
    # Process the file
    print("\nProcessing...")
    update_adif_file(input_file, output_file, field_name, field_value)

    if chase_mode == 'Y':  #Run the update again adding the chased from gridsquare
        print(f"\nChase mode activated, modifying MY_GRIDSQUARE")
        input_file = default_output_file_name
        output_file = default_chase_file_name
        field_value = default_MY_GRIDSQUARE
        field_name = 'MY_GRIDSQUARE'
        print(f"Will add/update <{field_name}:{len(field_value)}>{field_value} to all records")
        print("\nProcessing...")
        update_adif_file(input_file, output_file, field_name, field_value)

    #how long did this run take
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Code execution took: {elapsed_time:.4f} seconds")

if __name__ == "__main__":
    main()