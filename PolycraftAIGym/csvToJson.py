import json, csv

with open('D:/Easy Pogo Recipes.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    data = []

    for row in csv_reader:
        output = {}
        input = {}
        if line_count == 0:
            print(f'Column names are {", ".join(row)}')
            line_count += 1
        else:
            output = {
                'item':row[1],
                'count':int(row[2])
            }

            for x in range(3, 22):
                if(x % 2 == 0):
                    s = 'slot' + str(int(x/2 - 1))
                    input.update({
                        s:{'item':row[x-1],
                        'count':int('0' + row[x])}
                    })
            data.append({
                'shapeless': row[0],
                'input': input,
                'output': output
            })
            line_count += 1
    r = {'recipes':data}
    r = json.dumps(r, indent=4)
    print(r)

